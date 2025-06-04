import re
import os
from constants import D_MAPPINGS, OUTPUT_DIR_BASE, D_VOLTAGES, D_PROCESSORS,D_SCHEDULES
from platform_config import PlatformConfig
from dse import exhaustive_search, iterative_search, directed_iterative_search
from simulations import analyze_results, single_sim, parallel_sims, contains_error

# Requires : // if FiringLatency > LatencyBound then self error("Latency is diverging. Throughput constraint is not met.") fi;

# =====================
# Analyze the original config
# =====================

# Define an initial platform configuration
def analyse_original():
    original_config = PlatformConfig(
        configName="original",
        dMapping={
            "MapTask1To":  "Node1", "MapTask2To":  "Node2", "MapTask3To":  "Node3",
            "MapTask4To":  "Node4", "MapTask5To":  "Node5", "MapTask6To":  "Node6",
            "MapTask7To":  "Node1", "MapTask8To":  "Node2", "MapTask9To":  "Node3",
            "MapTask10To": "Node4", "MapTask11To": "Node5"
        },
        dPriority={f"PriorityTask{i}": str(i) for i in range(1, 12)},
        dProcessors={f"Node{i}ProcessorType": "ARMv8" if i % 2 else "Adreno" for i in range(1, 7)},
        dSchedules={f"OSPolicy{i}": "FCFS" if i < 4 else "PB" for i in range(1, 7)},
        dVoltageScales={f"VSF{i}": "1.0/1.0" for i in range(1, 7)},
    )

    # Run a single simulation
    single_sim(original_config)

    # Analyze results after simulation completion
    energy, avgLatency, throughput = analyze_results(original_config)
    if energy and avgLatency and throughput:
        print(f"Config {original_config.configName} has attributes:\n\tEnergy:     {energy}\n\tAvg latency:{avgLatency}\n\tThroughput: {throughput}")

# =====================
# Benchmarking 
# =====================

def run_benchmark(*lNumOfNodes):
    lInitials = [PlatformConfig(
        dMapping=D_MAPPINGS[f"{n}Nodes"],
        dPriority={f"PriorityTask{i}": str(i) for i in range(1, 12)},
        dProcessors={f"Node{i}ProcessorType": "Adreno" for i in range(1, n+1)},
        dSchedules={f"OSPolicy{i}": "FCFS" for i in range(1, n+1)},
        dVoltageScales={f"VSF{i}": "1.0/1.0" for i in range(1, n+1)},
    ) for n in lNumOfNodes]

    # Run a single simulation
    parallel_sims(lInitials)

    # Analyze results after simulation completion
    for config in lInitials:
        energy, avgLatency, throughput = analyze_results(config)
        if energy and avgLatency and throughput:
            print(f"Config {config.configName} has attributes:\n\tEnergy:     {energy}\n\tAvg latency:{avgLatency}\n\tThroughput: {throughput}")

# =====================
# Exhaustive search
# =====================

def exhaustive_search(*lNumOfNodes):
    # Generate the configuration tree
    dConfigs = {}

    for i in lNumOfNodes:
        dConfigs[f"{i}Nodes"] = exhaustive_search(i, dryRun=False)

# =====================
# Iterative search
# =====================

def perform_iterative_search(lNumOfNodes, dryRun=True, winnerSampleSize=1, iterations=1):
    sWinners = set()
    for  numOfNodes in lNumOfNodes:
        sWinners = sWinners.union(iterative_search(numOfNodes, winnerSampleSize, iterations, dryRun))

def perform_directed_iterative_search(dryRun=True, winnerSampleSize=1, iterations=1, maxDepth=1, *lNumOfNodes):
    sWinners = set()
    for  numOfNodes in lNumOfNodes:
        sWinners = sWinners.union(directed_iterative_search(numOfNodes, winnerSampleSize, iterations, dryRun, maxDepth))

# =====================
# Testing of Task Graph Modifications
# =====================

def perform_task_merging(lConfigs):
    parallel_sims(lConfigs)

    for config in lConfigs:
        print(config.outputDir.joinpath("stderr.txt").read_text())
        config.write_results_to_csv(OUTPUT_DIR_BASE.joinpath(f"original_application_transformation.csv"))


# Original simulation with graph alterations applied
dMergedConfigs = {
    "application3_8": PlatformConfig(
        configName="config_3_8",
        dProcessors={f"Node{i}ProcessorType": "ARMv8" for i in range(1, 7)},
        dSchedules={f"OSPolicy{i}": "FCFS" for i in range(1, 7)},
        dVoltageScales={f"VSF{i}": "1.0/1.0" for i in range(1, 7)},
        dPriority={f"PriorityTask{task}": str(i) for i, task in enumerate(["1", "2", "3_8", "4", "5", "6", "7", "9", "10", "11"])},
        dMapping={
            "MapTask1To":  "Node1", "MapTask2To":  "Node2", "MapTask3_8To":  "Node3", 
            "MapTask4To":  "Node4", "MapTask5To":  "Node5", "MapTask6To":    "Node6", 
            "MapTask7To":  "Node1", "MapTask9To":  "Node3", "MapTask10To":   "Node4", 
            "MapTask11To": "Node5"
        }
    ),
    "application5_6": PlatformConfig(
        configName="config_5_6",    
        dProcessors={f"Node{i}ProcessorType": "ARMv8" for i in range(1, 7)},
        dSchedules={f"OSPolicy{i}": "FCFS" for i in range(1, 7)},
        dVoltageScales={f"VSF{i}": "1.0/1.0" for i in range(1, 7)},
        dPriority={f"PriorityTask{task}": str(i) for i, task in enumerate(["1", "2", "3", "4", "5_6", "7", "8", "9", "10", "11"])},
        dMapping={
            "MapTask1To":  "Node1", "MapTask2To":   "Node2",   "MapTask3To":  "Node3", 
            "MapTask4To":  "Node4", "MapTask5_6To": "Node5_6", "MapTask7To":  "Node1",
            "MapTask8To":  "Node2", "MapTask9To":   "Node3",   "MapTask10To": "Node4", 
            "MapTask11To": "Node5"
        }
    ),

    "application5_9": PlatformConfig(
        configName="config_5_9",    
        dProcessors={f"Node{i}ProcessorType": "ARMv8" for i in range(1, 7)},
        dSchedules={f"OSPolicy{i}": "FCFS" for i in range(1, 7)},
        dVoltageScales={f"VSF{i}": "1.0/1.0" for i in range(1, 7)},
        dPriority={f"PriorityTask{task}": str(i) for i, task in enumerate(["1", "2", "3", "4", "5_9", "6", "7", "8", "10", "11"])},
        dMapping={
            "MapTask1To":  "Node1", "MapTask2To":  "Node2",   "MapTask3To":  "Node3", 
            "MapTask4To":  "Node4", "MapTask5_9To":"Node5_9", "MapTask6To":  "Node6", 
            "MapTask7To":  "Node1", "MapTask8To":  "Node2",   "MapTask10To": "Node4", 
            "MapTask11To": "Node5"
        }
    ),
    "application7_8": PlatformConfig(
        configName="config_7_8",    
        dProcessors={f"Node{i}ProcessorType": "ARMv8" for i in range(1, 7)},
        dSchedules={f"OSPolicy{i}": "FCFS" for i in range(1, 7)},
        dVoltageScales={f"VSF{i}": "1.0/1.0" for i in range(1, 7)},
        dPriority={f"PriorityTask{task}": str(i) for i, task in enumerate(["1", "2", "3", "4", "5", "6", "7_8", "9", "10", "11"])},
        dMapping={
            "MapTask1To":   "Node1", "MapTask2To":  "Node2", "MapTask3To":  "Node3", 
            "MapTask4To":   "Node4", "MapTask5To":  "Node5", "MapTask6To":  "Node6", 
            "MapTask7_8To": "Node1", "MapTask9To":  "Node3", "MapTask10To": "Node4",
            "MapTask11To":  "Node5"
        }
    )
}

for key in dMergedConfigs.keys():
    dMergedConfigs[key].applicationType = key

# =====================
# Alter Mappings
# =====================

ddMappings = {
    "MI_Ad_Ad_AR": {
        # ARMv8
        "MapTask1To":  "Node4", 
        "MapTask4To":  "Node4",  
        "MapTask8To":  "Node4",   
        # Adreno
        "MapTask2To":  "Node2", 
        "MapTask5To":  "Node2", 
        "MapTask6To":  "Node3",
        "MapTask9To":  "Node2", 
        "MapTask10To": "Node3",       
        # MIPS
        "MapTask3To":  "Node1",
        "MapTask7To":  "Node1",
        "MapTask11To": "Node1"
        
    },
    
    "MI_Ad_Ad_Ad":{
        # Adreno
        "MapTask1To":  "Node4", 
        "MapTask2To":  "Node4", 
        "MapTask3To":  "Node2",
        "MapTask4To":  "Node3",  
        "MapTask5To":  "Node4", 
        "MapTask6To":  "Node2",
        "MapTask7To":  "Node3",
        # MIPS
        "MapTask8To":  "Node1", 
        "MapTask9To":  "Node1",        
        "MapTask10To": "Node1",
        "MapTask11To": "Node1"
    },
    
    "Ad_Ad_Ad_Ad": {
        # Adreno
        "MapTask1To":  "Node1", 
        "MapTask2To":  "Node2", 
        "MapTask3To":  "Node3",
        "MapTask4To":  "Node4",  
        "MapTask5To":  "Node1", 
        "MapTask6To":  "Node2",
        "MapTask7To":  "Node3",
        "MapTask8To":  "Node4", 
        "MapTask9To":  "Node1",        
        "MapTask10To": "Node2",
        "MapTask11To": "Node3"
    },
    
    "MI_Ad_Ad_MI":{
        # Adreno
        "MapTask1To":  "Node1", 
        "MapTask4To":  "Node4",  
        "MapTask5To":  "Node1", 
        "MapTask6To":  "Node4",
        "MapTask9To":  "Node1",        
        # MIPS
        "MapTask2To":  "Node2", 
        "MapTask3To":  "Node3",
        "MapTask7To":  "Node2",
        "MapTask8To":  "Node3", 
        "MapTask10To": "Node2",
        "MapTask11To": "Node3"
    },

    "Ad_Ad_Ad_MI":{
        # Adreno
        "MapTask1To":  "Node1", 
        "MapTask2To":  "Node1", 
        "MapTask3To":  "Node2",
        "MapTask4To":  "Node3",  
        "MapTask5To":  "Node1", 
        "MapTask6To":  "Node2",
        "MapTask7To":  "Node3",
        # MIPS
        "MapTask8To":  "Node4", 
        "MapTask9To":  "Node4",        
        "MapTask10To": "Node4",
        "MapTask11To": "Node4"
    },

    "Ad_MI_MI_MI_MI":{
        # Adreno
        "MapTask1To":  "Node1", 
        "MapTask4To":  "Node1",  
        "MapTask8To":  "Node1",       
        # MIPS
        "MapTask2To":  "Node2", 
        "MapTask3To":  "Node3",
        "MapTask5To":  "Node4", 
        "MapTask6To":  "Node5",
        "MapTask7To":  "Node2",
        "MapTask9To":  "Node3",  
        "MapTask10To": "Node4",
        "MapTask11To": "Node5"
    },

    "Ad_MI_MI_MI_Ad":{
        # Adreno
        "MapTask1To":  "Node5", 
        "MapTask4To":  "Node1",  
        "MapTask8To":  "Node5",
        "MapTask5To":  "Node1", 
        "MapTask6To":  "Node1",       
        # MIPS
        "MapTask2To":  "Node2", 
        "MapTask3To":  "Node4",
        "MapTask7To":  "Node2",
        "MapTask9To":  "Node4",  
        "MapTask10To": "Node2",
        "MapTask11To": "Node4"
    },

    "Ad_MI_Ad_MI_MI":{
        # Adreno
        "MapTask1To":  "Node3", 
        "MapTask4To":  "Node1",  
        "MapTask8To":  "Node3",
        "MapTask5To":  "Node1", 
        "MapTask6To":  "Node1",       
        # MIPS
        "MapTask2To":  "Node2", 
        "MapTask3To":  "Node4",
        "MapTask7To":  "Node5",
        "MapTask9To":  "Node4",  
        "MapTask10To": "Node2",
        "MapTask11To": "Node5"
    },

    "Ad_MI_Ad_MI_Ad":{
        # Adreno
        "MapTask1To":  "Node1", 
        "MapTask2To":  "Node1", 
        "MapTask3To":  "Node3",
        "MapTask4To":  "Node5",  
        "MapTask5To":  "Node1", 
        "MapTask6To":  "Node3",
        "MapTask7To":  "Node5",
        # MIPS
        "MapTask8To":  "Node2", 
        "MapTask9To":  "Node4",        
        "MapTask10To": "Node2",
        "MapTask11To": "Node4"
    }
}

def create_config(name, dMapping, lPriority = None):
    nodes, arch, sched, volt = re.split(r'-', name)
    nodes = str(nodes[1])
    lProc = re.split(r'_', arch.replace("P", ""))
    lSched = re.split(r'_', sched.replace("S", ""))
    lVolt = re.split(r'_', volt.replace("V", ""))
    
    return PlatformConfig(
        dProcessors={f"Node{i+1}ProcessorType": D_PROCESSORS[proc] for i, proc in enumerate(lProc)},
        dSchedules={f"OSPolicy{i+1}": D_SCHEDULES[sched]  for i, sched in enumerate(lSched)},
        dVoltageScales={f"VSF{i+1}": D_VOLTAGES[volt]  for i, volt in enumerate(lVolt)},
        dPriority={f"PriorityTask{i+1}": str(i+1) if lPriority is None else str(lPriority[i]) for i in range(0,11)},
        dMapping=dMapping
    )

def altered_mappings(sWinners):
    lConfigs =[]

    for winner in sWinners:
        if winner.config.configName.find("N4") != -1:
            lConfigs.append(create_config(winner.config.configName, ddMappings["MI_Ad_Ad_AR"]))
            lConfigs.append(create_config(winner.config.configName, ddMappings["MI_Ad_Ad_Ad"]))
            lConfigs.append(create_config(winner.config.configName, ddMappings["Ad_Ad_Ad_Ad"]))
            lConfigs.append(create_config(winner.config.configName, ddMappings["MI_Ad_Ad_MI"]))
            lConfigs.append(create_config(winner.config.configName, ddMappings["Ad_Ad_Ad_MI"]))

        elif winner.config.configName.find("N5") != -1:
            lConfigs.append(create_config(winner.config.configName, ddMappings["Ad_MI_MI_MI_MI"]))
            lConfigs.append(create_config(winner.config.configName, ddMappings["Ad_MI_MI_MI_Ad"]))
            lConfigs.append(create_config(winner.config.configName, ddMappings["Ad_MI_Ad_MI_MI"]))
            lConfigs.append(create_config(winner.config.configName, ddMappings["Ad_MI_Ad_MI_Ad"]))

    parallel_sims(lConfigs)

    if os.path.isfile(OUTPUT_DIR_BASE.joinpath(f"altered_mapping.csv")):
        os.remove(OUTPUT_DIR_BASE.joinpath(f"altered_mapping.csv"))
        
    for config in lConfigs:
        if not contains_error(config):
            analyze_results(config)
            config.write_results_to_csv(OUTPUT_DIR_BASE.joinpath(f"altered_mapping.csv"))
        
    del lConfigs
    
# =====================
# Update Priority
# =====================

if os.path.isfile(OUTPUT_DIR_BASE.joinpath(f"priority_based_search.csv")):
    os.remove(OUTPUT_DIR_BASE.joinpath(f"priority_based_search.csv"))
   
def get_priority_configs(lWinners):
    # T 2 3 4 
    lT234 = [
        [2, 3, 4],
        [2, 4, 3],
        [3, 2, 4],
        [3, 4, 2],
        [4, 2, 3],
        [4, 3, 2]
    ]

    # T 5 6 7 8
    lT5678 = [
        [5, 6, 7, 8],
        [5, 6, 8, 7],
        [5, 7, 6, 8],
        [5, 7, 8, 6],
        [5, 8, 6, 8],
        [5, 8, 8, 6],
        [6, 5, 7, 8],
        [6, 5, 8, 7],
        [6, 7, 5, 8],
        [6, 7, 8, 5],
        [6, 8, 5, 8],
        [6, 8, 8, 5],
        [7, 6, 5, 8],
        [7, 6, 8, 5],
        [7, 5, 6, 8],
        [7, 5, 8, 6],
        [7, 8, 6, 8],
        [7, 8, 8, 6],
        [8, 6, 7, 5],
        [8, 6, 5, 7],
        [8, 7, 6, 5],
        [8, 7, 5, 6],
        [8, 5, 6, 5],
        [8, 5, 5, 6]
    ]

    # T 9 10
    lT910 = [
        [9, 10],
        [10, 9]
    ]

    llPriorityConfigs = []

    for start in lT234:
        for mid in lT5678:
            for end in lT910:
                for winner in lWinners:
                    if winner.find("N4") != -1 :
                        llPriorityConfigs.append(create_config(winner, ddMappings["MI_Ad_Ad_MI"], [1] + start + mid + end + [11]))
                        llPriorityConfigs.append(create_config(winner, ddMappings["Ad_Ad_Ad_MI"], [1] + start + mid + end + [11]))
                        llPriorityConfigs.append(create_config(winner, ddMappings["MI_Ad_Ad_Ad"], [1] + start + mid + end + [11]))

    return

def perform_priority_tests(lConfigs: list):
    if len(lConfigs) >= 100:
        lSims = [lConfigs.pop(0) for i in range(100)]
        
        parallel_sims(lSims)
        
        for config in lSims:
            if not contains_error(config):
                analyze_results(config)
                config.write_results_to_csv(OUTPUT_DIR_BASE.joinpath(f"priority_based_search.csv"))
        
        del lSims
        
