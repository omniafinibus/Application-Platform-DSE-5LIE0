import os
from copy import deepcopy
from copy import copy
from collections import deque
from dataclasses import dataclass, field
from platform_config import PlatformConfig
from simulations import analyze_results, parallel_sims, contains_error, single_sim
from constants import (
    L_PROCESSORS,
    L_SCHEDULES,
    L_VOLTAGE_SCALES,
    D_MAPPINGS,
    OUTPUT_DIR_BASE,
)


@dataclass
class ConfigNode:
    def __init__(self, parent, config: PlatformConfig):
        self.lChildren = []
        self.parent = parent
        self.config = config
        self.depth = 0
        self.avgLatency = 0
        self.throughput = 0
        self.energy = 0
        self.analyzed = False

    def analyze(self):
        self.energy, self.avgLatency, self.throughput = analyze_results(self.config)
        if self.energy and self.avgLatency and self.throughput:
            self.analyzed = True
            return self.energy, self.avgLatency, self.throughput
        else:
            return False

    def __hash__(self):
        """
        Generates a unique hash for the configuration based on its attributes.
        This ensures duplicate configurations are not added to the tree.
        """
        if isinstance(self.config, DryConfig):
            return hash(
                (
                    frozenset(self.config.dProcessors.items()),
                    frozenset(self.config.dSchedules.items()),
                    frozenset(self.config.dVoltageScales.items()),
                )
            )
        elif isinstance(self.config, PlatformConfig):
            return hash(
                (
                    frozenset(self.config.dMapping.items()),
                    frozenset(self.config.dProcessors.items()),
                    frozenset(self.config.dSchedules.items()),
                    frozenset(self.config.dVoltageScales.items()),
                )
            )

    def __eq__(self, other):
        """
        Checks equality between two ConfigNode objects based on their configurations.
        """
        if isinstance(self.config, DryConfig):
            return (
                self.config.dProcessors == other.config.dProcessors
                and self.config.dSchedules == other.config.dSchedules
                and self.config.dVoltageScales == other.config.dVoltageScales
            )
        elif isinstance(self.config, PlatformConfig):
            return (
                self.config.dMapping == other.config.dMapping
                and self.config.dProcessors == other.config.dProcessors
                and self.config.dSchedules == other.config.dSchedules
                and self.config.dVoltageScales == other.config.dVoltageScales
            )


@dataclass
class DryConfig:
    dProcessors: dict = field(default_factory=dict)
    dSchedules: dict = field(default_factory=dict)
    dVoltageScales: dict = field(default_factory=dict)
    depth: int = 0

    def __hash__(self):
        """
        Generates a unique hash for the configuration based on its attributes.
        This ensures duplicate configurations are not added to the tree.
        """
        return hash(
            (
                frozenset(self.dProcessors.items()),
                frozenset(self.dSchedules.items()),
                frozenset(self.dVoltageScales.items()),
            )
        )

    def __eq__(self, other):
        """
        Checks equality between two ConfigNode objects based on their configurations.
        """
        return (
            self.dProcessors == other.dProcessors
            and self.dSchedules == other.dSchedules
            and self.dVoltageScales == other.dVoltageScales
        )


@dataclass
class IterationConfig:
    sInitialConfigNodes: set = field(default_factory=set)
    configTree: ConfigNode = None
    lConfigNodes: list = field(default_factory=list)
    sWinnerNodes: dict = field(default_factory=dict)


def get_child_single_change(
    parent: ConfigNode, newValueKey: str, newValue, attrib: str
):
    newAttrib = copy(parent.config.__dict__[attrib])
    newAttrib[newValueKey] = newValue

    if isinstance(parent.config, DryConfig):
        child = ConfigNode(
            parent=parent,
            config=DryConfig(
                parent.config.dProcessors,
                parent.config.dSchedules,
                parent.config.dVoltageScales,
            ),
        )
        child.depth = 0
        child.config.__dict__[attrib] = newAttrib

    elif isinstance(parent.config, PlatformConfig):
        child = ConfigNode(
            parent=parent,
            config=PlatformConfig(
                parent.config.dMapping,
                parent.config.dPriority,
                parent.config.dProcessors,
                parent.config.dSchedules,
                parent.config.dVoltageScales,
            ),
        )
        child.config.__dict__[attrib] = newAttrib
        child.depth = 0
        child.config._get_name()
    else:
        Exception(f"Config type is unknown: {parent.config}")

    return child


def get_root(dryRun, numOfNodes):
    # Start with the base configuration (default values)
    if dryRun:
        return ConfigNode(
            parent=None,
            config=DryConfig(
                dProcessors={
                    f"Proc{i}": L_PROCESSORS[0] for i in range(1, numOfNodes + 1)
                },
                dSchedules={
                    f"Poli{i}": L_SCHEDULES[0] for i in range(1, numOfNodes + 1)
                },
                dVoltageScales={
                    f"Volt{i}": L_VOLTAGE_SCALES[0] for i in range(1, numOfNodes + 1)
                },
            ),
        )
    else:
        return ConfigNode(
            parent=None,
            config=PlatformConfig(
                dMapping=D_MAPPINGS[f"{numOfNodes}Nodes"],
                dPriority={f"PriorityTask{i}": str(i) for i in range(1, 12)},
                dProcessors={
                    f"Node{i}ProcessorType": L_PROCESSORS[0]
                    for i in range(1, numOfNodes + 1)
                },
                dSchedules={
                    f"OSPolicy{i}": L_SCHEDULES[0] for i in range(1, numOfNodes + 1)
                },
                dVoltageScales={
                    f"VSF{i}": L_VOLTAGE_SCALES[0] for i in range(1, numOfNodes + 1)
                },
            ),
        )


def generate_config_tree(
    root, numOfNodes, maxDepth: int = 10, lPreviousConfigs: set = None
):
    """
    Generates a tree of configurations where each child differs by at most one change.

    Returns:
        ConfigNode: Root node of the configuration tree.
    """
    numOfNodes = len(set(D_MAPPINGS[f"{numOfNodes}Nodes"].values()))

    queue = deque([(0, root)])  # Use a queue for BFS traversal
    visitedConfigs = {root}  # Store visited configurations to avoid duplicates
    if lPreviousConfigs is not None:
        visitedConfigs = visitedConfigs.union(lPreviousConfigs)

    while queue:
        depth, current = queue.popleft()

        # Generate child configurations by making one change at a time
        for targetAttrib, lOptions in [
            ("dProcessors", L_PROCESSORS),
            ("dSchedules", L_SCHEDULES),
            ("dVoltageScales", L_VOLTAGE_SCALES),
        ]:
            for node, currentAttrib in current.config.__dict__[targetAttrib].items():
                for newValue in lOptions:
                    if newValue != currentAttrib:  # Change only if different
                        child = get_child_single_change(
                            current, node, newValue, targetAttrib
                        )
                        if child not in visitedConfigs and depth < maxDepth:
                            current.lChildren.append(child)
                            queue.append((depth + 1, child))
                            visitedConfigs.add(child)

        # Remove added lPreviousConfigs
        visitedConfigs = (
            visitedConfigs
            if lPreviousConfigs is None
            else visitedConfigs.difference(lPreviousConfigs)
        )

    return root, len(visitedConfigs), visitedConfigs


def exhaustive_search(numOfNodes, dryRun: bool = True):
    configTree, numOfConfigs, lConfigNodes = generate_config_tree(
        get_root(dryRun, numOfNodes), numOfNodes, 10000000
    )
    testName = f"exhaustive_search_{numOfNodes}_nodes.csv"
    lConfigs = [node.config for node in lConfigNodes]

    print(f"{numOfNodes}Nodes has {numOfConfigs} configs")

    if not dryRun:
        parallel_sims(lConfigs)

        for config in lConfigs:
            energy, avgLatency, throughput = analyze_results(config)
            if energy and avgLatency and throughput:
                config.write_results_to_csv(
                    OUTPUT_DIR_BASE.joinpath(testName)
                )

    return configTree, numOfConfigs, lConfigs


def get_geometric_mean(*lInputs):
    result = 1
    for input in lInputs:
        result *= input
    return result ** (1 / len(lInputs))


def get_winners(sConfigNodes, winnerSampleSize, dryRun: bool = True, maxDepth:int = 5):
    numOfConfig = len(sConfigNodes)
    
    sHealthyNodes = set()
    for node in sConfigNodes:
        if not contains_error(node.config):
            sHealthyNodes.add(node)

    if numOfConfig <= winnerSampleSize:
        return sHealthyNodes
    elif dryRun:
        newSet = {sConfigNodes.pop() for i in range(winnerSampleSize)}
        sConfigNodes = sConfigNodes.union(newSet)
        return newSet    
    else:
        lHealthyConfigs = []

        for node in sHealthyNodes:
            if not node.analyzed:
                node.analyze()

            if node.analyzed and node.depth < maxDepth:
                lHealthyConfigs.append(
                    (
                        get_geometric_mean(
                            1/node.energy, 1/node.avgLatency, node.throughput
                        ),
                        node,
                    )
                )

        lHealthyConfigs.sort(key=lambda x: x[0])
        return set([config[1] for config in lHealthyConfigs[0:winnerSampleSize]])


def iterative_search(
    numOfNodes, winnerSampleSize, iterations: int = 10, dryRun: bool = True
):
    sAllWinners = set()
    testName = f"iterative_search_depth_{iterations}_sampsize_{winnerSampleSize}_{numOfNodes}_nodes.csv"
    
    dIterations = {it: IterationConfig() for it in range(iterations)}

    if not dryRun and os.path.isfile(OUTPUT_DIR_BASE.joinpath(testName)):
        os.remove(OUTPUT_DIR_BASE.joinpath(testName))
        
    configTreeRoot = get_root(dryRun, numOfNodes)
    if not dryRun:
        single_sim(configTreeRoot.config)
    sWinnerNodes = {configTreeRoot}

    if not dryRun and os.path.isfile(
        OUTPUT_DIR_BASE.joinpath(testName)
    ):
        os.remove(OUTPUT_DIR_BASE.joinpath(testName))

    if configTreeRoot.analyze():
        configTreeRoot.config.write_results_to_csv(
            OUTPUT_DIR_BASE.joinpath(testName)
        )
        message = f"# Root geometric mean is: {get_geometric_mean(configTreeRoot.throughput, 1/configTreeRoot.avgLatency, 1/configTreeRoot.energy)} #"
        print("".join(["#" for i in range(len(message))]))
        print(message)
        print("".join(["#" for i in range(len(message))]))
        
    else:
        message = f"\nRoot could not be analyzed.\n"
        print("".join(["#" for i in range(len(message))]))
        print(message)
        print("".join(["#" for i in range(len(message))]))

    for it, iterationConfig in dIterations.items():
        sTestedConfigs = set()
        for winner in sWinnerNodes:
            sTestedConfigs.add(winner)
            # Generate configs which will be explored
            root, numOfConfigs, lConfigNodes = generate_config_tree(
                winner, numOfNodes, 1, sTestedConfigs
            )

            if not dryRun:
                for node in lConfigNodes:
                    node.config.set_iteration(it)

            iterationConfig.lConfigNodes += lConfigNodes

        message = f"{numOfNodes} Nodes, iteration {it} has {len(iterationConfig.lConfigNodes)} configs"
        
        # Update shared lists
        print("\n" + message)
        print("".join(["=" for i in range(len(message))]))

        if dryRun:
            sTestedConfigs = sTestedConfigs.union(lConfigNodes)
            sTestedConfigs = sTestedConfigs.union(sWinnerNodes)
            sWinnerNodes = get_winners(iterationConfig.lConfigNodes, winnerSampleSize, dryRun)
        else:
            runSims = parallel_sims(
                [node.config for node in iterationConfig.lConfigNodes]
            )
            sTestedConfigs = sTestedConfigs.union(lConfigNodes)
            sTestedConfigs = sTestedConfigs.union(sWinnerNodes)

            numOfConfigsWithError = 0
            for config in [node.config for node in sTestedConfigs]:
                if contains_error(config):
                    numOfConfigsWithError += 1
                else:
                    analyze_results(config)
                    if config.get_metrics():
                        config.write_results_to_csv(
                            OUTPUT_DIR_BASE.joinpath(testName)
                        )
            print(
                f"Out of {len(iterationConfig.lConfigNodes)} configs\n\t{len(runSims)} ran\n\t{len(iterationConfig.lConfigNodes) - len(runSims)} were already done\n\t{numOfConfigsWithError} ended with an error\n\t{len(iterationConfig.lConfigNodes) - numOfConfigsWithError} were successful\n"
            )

            sWinnerNodes = get_winners(
                iterationConfig.lConfigNodes, winnerSampleSize,
                dryRun
            )
            sAllWinners = sAllWinners.union(sWinnerNodes)

    return sAllWinners


def directed_iterative_search(
    numOfNodes, winnerSampleSize, iterations: int = 10, dryRun: bool = True, maxDepth:int = 10
):
    sAllWinners = set()
    testName = f"directed_iterative_search_depth_{iterations}_sampsize_{winnerSampleSize}_{numOfNodes}_nodes.csv"
    
    dIterations = {it: IterationConfig() for it in range(iterations)}

    # Run initial root
    configTreeRoot = get_root(dryRun, numOfNodes)
    
    if not dryRun:
        single_sim(configTreeRoot.config)
    sWinnerNodes = {configTreeRoot}

    if not dryRun and os.path.isfile(
        OUTPUT_DIR_BASE.joinpath(testName)
    ):
        os.remove(OUTPUT_DIR_BASE.joinpath(testName))

    if configTreeRoot.analyze():
        configTreeRoot.config.write_results_to_csv(
            OUTPUT_DIR_BASE.joinpath(testName)
        )
        message = f"# Root geometric mean is: {get_geometric_mean(configTreeRoot.throughput, 1/configTreeRoot.avgLatency, 1/configTreeRoot.energy)} #"
        print("".join(["#" for i in range(len(message))]))
        print(message)
        print("".join(["#" for i in range(len(message))]))
        
    else:
        f"\nRoot could not be analyzed.\n"
        print("".join(["#" for i in range(len(message))]))
        print(message)
        print("".join(["#" for i in range(len(message))]))

    for it, iterationConfig in dIterations.items():
        sTestedConfigs = set()
        for winner in sWinnerNodes:
            sTestedConfigs.add(winner)
            # Increase the depth of this winner
            winner.depth += 1

            # Generate configs which will be explored
            root, numOfConfigs, lConfigNodes = generate_config_tree(
                winner, numOfNodes, winner.depth, sTestedConfigs
            )

            if not dryRun:
                for node in lConfigNodes:
                    node.config.set_iteration(it)

            iterationConfig.lConfigNodes += lConfigNodes

        message = f"{numOfNodes} Nodes, iteration {it} has {len(iterationConfig.lConfigNodes)} configs"
        
        # Update shared lists
        print("\n" + message)
        print("".join(["=" for i in range(len(message))]))

        if dryRun:
            sTestedConfigs = sTestedConfigs.union(lConfigNodes)
            sTestedConfigs = sTestedConfigs.union(sWinnerNodes)
            sWinnerNodes = get_winners(sTestedConfigs, winnerSampleSize, dryRun)
        else:
            runSims = parallel_sims(
                [node.config for node in iterationConfig.lConfigNodes]
            )
            sTestedConfigs = sTestedConfigs.union(lConfigNodes)
            sTestedConfigs = sTestedConfigs.union(sWinnerNodes)

            numOfConfigsWithError = 0
            for config in [node.config for node in sTestedConfigs]:
                if contains_error(config):
                    numOfConfigsWithError += 1
                else:
                    analyze_results(config)
                    if config.get_metrics():
                        config.write_results_to_csv(
                            OUTPUT_DIR_BASE.joinpath(testName)
                        )

            print(
                f"Out of {len(iterationConfig.lConfigNodes)} configs\n\t{len(runSims)} ran\n\t{len(iterationConfig.lConfigNodes) - len(runSims)} were already done\n\t{numOfConfigsWithError} ended with an error\n\t{len(iterationConfig.lConfigNodes) - numOfConfigsWithError} were successful\n"
            )

            sWinnerNodes = deepcopy(get_winners(sTestedConfigs, winnerSampleSize,dryRun,maxDepth))
            del sTestedConfigs
        sAllWinners = sAllWinners.union(sWinnerNodes)

        for i, winner in enumerate(sWinnerNodes):
            print(
                f"\tWinner {i} with with geo-mean {get_geometric_mean(winner.throughput, 1/winner.avgLatency, 1/winner.energy)}:\t {winner.config.configName}:"
            )
            
        return sAllWinners