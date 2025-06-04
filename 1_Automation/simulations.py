import os
import shutil
from pathlib import Path
from timing import TaskTiming
from tqdm import tqdm
from multiprocessing import Pool
import xml.etree.ElementTree as et
from Rotalumis import rotalumisrunner  # External tool for simulation execution
from platform_config import PlatformConfig
from constants import MODEL_DIR, MODEL_LIB_DIRS


# =====================
# Simulation Methods
# =====================

def contains_error(config):
    
    dir = config.outputDir.joinpath("stderr.txt")
    if os.path.isfile(dir):
        text = dir.read_text()
        return len(text) > 2
    else:
        return False

def run_simulation(selectedConfig: PlatformConfig):
    """ 
    Runs the simulation for a given platform configuration.
    Args:
        selectedConfig (PlatformConfig): The platform configuration to simulate.

    Returns:
        tuple: (Simulation result, selectedConfig, output directory)
    """
    model = selectedConfig.get_model()  # Generate the model from the template
    
    # Ensure the output directory exists
    if not os.path.isdir(selectedConfig.outputDir):
        os.makedirs(selectedConfig.outputDir)
        
        # Copy processor configuration files into the output directory
        for proc in ["ARMv8.txt", "MIPS.txt", "Adreno.txt"]:
            shutil.copy(MODEL_DIR.joinpath("simulator", proc),
                selectedConfig.outputDir.joinpath(proc)
            )
    
    # Write the generated model to a temporary file
    temp_filename = selectedConfig.outputDir.joinpath("model.poosl")
    with open(temp_filename, "w") as output:
        output.write(model)
    
    temp_path = os.path.abspath(temp_filename)  # Get the absolute path to the model file
    
    # Execute the simulation using Rotalumis
    return rotalumisrunner.runrotalumis(temp_path, selectedConfig.outputDir, MODEL_LIB_DIRS), selectedConfig, selectedConfig.outputDir

def single_sim(config: PlatformConfig, force:bool = False):
    """ 
    Runs a single simulation instance.

    Uses multiprocessing to execute the simulation and handles errors.

    Args:
        config (PlatformConfig): The configuration to simulate.
    """
    # Check if output files already exists, if they do skip the simulation
    if not contains_error(config):
        if force or not os.path.isdir(config.outputDir) and not all(
            [os.path.isfile(config.outputDir.joinpath("BatteryTrace.xml"))] + 
            [os.path.isfile(config.outputDir.joinpath(f"ProcessorTraceNode{i}.xml")) for i in range(1, config.numOfNodes + 1)]
            ):
            with Pool() as pool:
                for (errcode, error), p, dir in tqdm(
                    pool.imap_unordered(run_simulation, [config]),  # Run the simulation in parallel
                    total=1,
                    desc="Running Simulation",
                ):
                    if errcode != 0:
                        # Handle errors if the simulation did not complete successfully
                        message = (
                            f"Model with params {p} returned {errcode} and did not terminate to completion.\n"
                            f"Check the output in {Path(dir).absolute()}\nLast error was:\n{error}"
                        )
                        print(message)
                        raise Exception(message)

    print("Experiment finished")

def parallel_sims(lConfigs: list, force:bool = False):
    """ 
    Runs multiple simulations in parallel.

    Args:
        lConfigs (list): A list of PlatformConfig objects to simulate.
    """
    
    lSims = []
    for config in lConfigs:
        if force or not os.path.isdir(config.outputDir):
            # print(f"Checking file {config.outputDir.joinpath("stderr.txt")}")
            if not contains_error(config):
                # print(f"\tAdded")
                lSims.append(config)
            # else:
            #     print(f"\tSkipped")
                
        
    with Pool() as pool:
        for (errcode, error), p, dir in tqdm(
            pool.imap_unordered(run_simulation, lSims),
            total=len(lSims),
            desc="Running Simulations",
        ):
            if errcode != 0:
                # Handle errors if any of the simulations fail
                message = (
                    f"Model with params {p} returned {errcode} and did not terminate to completion.\n"
                    f"Check the output in {Path(dir).absolute()}\nLast error was:\n{error}"
                )
                # print(message)
                # if not '[ERROR  ] An exception occurred during run.\n[ERROR  ] Latency is diverging. Throughput constraint is not met.\n':
                #     raise Exception(message)

    print("Experiment finished")
    return lSims

def analyze_results(config: PlatformConfig):
    """ 
    Analyzes simulation results by parsing XML output files.

    Args:
        config (PlatformConfig): The configuration whose results should be analyzed.

    Returns:
        tuple: (power usage data, task execution trace data)
    """
    
    if contains_error(config):
        # print(f"Config {config.configName} has errors, no analysis is done")
        return False, False, False
    else :
        # Parse power usage data from the simulation output
        try:
            for power in et.parse(config.outputDir.joinpath("BatteryTrace.xml")).getroot():
                config._measPower.update_ltPower(power.attrib["difference"], power.attrib["time"])
        except:
            print(f"Measurmenet {config.configName} is fucked")
            raise Exception(f"Measurmenet {config.configName} is fucked")
        
        # Parse execution trace data for each node in the system
        lTaskExecutionData = {
            f"Node{i}": et.parse(config.outputDir.joinpath(f"ProcessorTraceNode{i}.xml")) 
            for i in range(1, config.numOfNodes + 1)
        }
        
        for node in lTaskExecutionData.values():
            lCurrentTasks = []
            lInterruptTime = []
            for child in node.getroot():
                time = float(child.attrib['time'])
                name = child.attrib['task']
                if 'start' in child.tag:
                    iteration = int(child.attrib['iteration'])
                    lTasks = list(filter(lambda x: (x.name == name and x.iteration == iteration), lCurrentTasks))
                    
                    # If the task was interrupted  
                    if len(lTasks) == 1:
                        # Remove the last interrupt time as that task has stopped
                        lTasks[0].down += time - lInterruptTime.pop(-1)
                        
                    # Mutliple tasks with the same name and iteration are present, this shouldnt happen
                    elif len(lTasks) > 1:
                        # Handle errors if any of the simulations fail
                        message = (f"Multiple tasks with the same iteration and name have been found")
                        print(message)
                        raise Exception(message)
                    
                    # A new task has started
                    else:
                        lCurrentTasks.append(TaskTiming(name=name, start=time, iteration=iteration))
                        
                        # The new task has interrupted another task
                        if len(lCurrentTasks) > 1:
                            # Add the start time to the end of the interrupt time, this list indicated the relation of interrupts and tasks
                            lInterruptTime.append(time)
                elif 'stop' in child.tag:
                    lTasks = list(filter(lambda x: (x.name == name), lCurrentTasks))
                    
                    # If the task was interrupted  
                    if len(lTasks) == 1:
                        # Remove the last interrupt time as that task has stopped
                        lTasks[0].stop = time
                        config.add_timing_meas(lTasks[0])
                        lCurrentTasks.remove(lTasks[0])
                        
                    # Mutliple tasks with the same name and iteration are present, this shouldnt happen
                    elif len(lTasks) > 1:
                        # Handle errors if any of the simulations fail
                        message = (f"Multiple tasks with the same name have been found")
                        print(message)
                        raise Exception(message)
                    
                    # A non existant task has been stopped
                    else:
                        # Handle errors if any of the simulations fail
                        message = (f"A non existant task has been stopped")
                        print(message)
                        raise Exception(message)
    
        return config.get_metrics()
