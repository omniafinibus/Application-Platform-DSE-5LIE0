from pathlib import Path

# =====================
# Configuration Constants
# =====================
# Define the base directory where simulation models and outputs are stored
BASE_DIR = Path('SET_DIR/')
MODEL_DIR = BASE_DIR.joinpath("0_POOSL_IDE")  # Path to the POOSL model directory
MODEL_LIB_DIRS = [MODEL_DIR]  # List of directories containing model libraries
OUTPUT_DIR_BASE = BASE_DIR.joinpath("1_Automation/output/")  # Base output directory

# Load the POOSL model template for design space exploration (DSE)
SIM_TIME = "0.1"  # Simulation runtime duration
MODEL_TEMPLATE = BASE_DIR.joinpath("1_Automation/templates/dse_template.poosl").read_text()
OPTI_ITERATIONS = 10

# =====================
# Config settings
# =====================
D_MAPPINGS = {
    "1Nodes":{
        "MapTask1To":  "Node1", "MapTask2To":  "Node1", "MapTask3To":  "Node1", "MapTask4To":  "Node1", "MapTask5To":  "Node1", "MapTask6To":  "Node1", "MapTask7To":  "Node1", "MapTask8To":  "Node1", "MapTask9To":  "Node1", "MapTask10To": "Node1", "MapTask11To": "Node1"
    },
    
    "2Nodes": {
        "MapTask1To":  "Node1", "MapTask2To":  "Node1", "MapTask3To":  "Node2", "MapTask4To":  "Node2", "MapTask5To":  "Node1", "MapTask6To":  "Node2", "MapTask7To":  "Node1", "MapTask8To":  "Node2", "MapTask9To":  "Node1", "MapTask10To": "Node2", "MapTask11To": "Node2"
    },
    
    "3Nodes": {
        "MapTask1To":  "Node1", "MapTask2To":  "Node1", "MapTask3To":  "Node2", "MapTask4To":  "Node3", "MapTask5To":  "Node1", "MapTask6To":  "Node2", "MapTask7To":  "Node3", "MapTask8To":  "Node3", "MapTask9To":  "Node2", "MapTask10To": "Node2", "MapTask11To": "Node3"
    },
    
    "4Nodes": {
        "MapTask1To":  "Node1", "MapTask2To":  "Node1", "MapTask3To":  "Node2", "MapTask4To":  "Node3", "MapTask5To":  "Node1", "MapTask6To":  "Node2", "MapTask7To":  "Node3", "MapTask8To":  "Node4", "MapTask9To":  "Node2", "MapTask10To": "Node4", "MapTask11To": "Node3"
    },
    
    "5Nodes": {
        "MapTask1To":  "Node1", "MapTask5To":  "Node1", "MapTask2To":  "Node2", "MapTask6To":  "Node2", "MapTask3To":  "Node3", "MapTask7To":  "Node3", "MapTask4To":  "Node4", "MapTask8To":  "Node4", "MapTask9To":  "Node4", "MapTask10To": "Node5", "MapTask11To": "Node5"
    },
    
    "6Nodes": {
        "MapTask1To":  "Node1", "MapTask2To":  "Node2", "MapTask3To":  "Node3", "MapTask4To":  "Node4", "MapTask5To":  "Node2", "MapTask6To":  "Node3", "MapTask7To":  "Node4", "MapTask8To":  "Node5", "MapTask9To":  "Node5", "MapTask10To": "Node6", "MapTask11To": "Node6"
    },
}

L_PROCESSORS = ["ARMv8", "MIPS", "Adreno"]

D_PROCESSORS = {
    "AR": "ARMv8", 
    "MI": "MIPS", 
    "Ad": "Adreno"
}

L_SCHEDULES = ["FCFS", "PB"]

D_SCHEDULES = {"FC": "FCFS", "PB": "PB"}

L_VOLTAGE_SCALES = ["1.0/1.0", "3.0/4.0", "2.0/3.0", "1.0/2.0", "1.0/3.0", "1.0/4.0"]

D_VOLTAGES = {
    "100": "1.0/1.0",
    "75": "3.0/4.0",
    "66": "2.0/3.0",
    "50": "1.0/2.0",
    "33": "1.0/3.0",
    "25": "1.0/4.0"
}

L_TASKS = ["Task1", "Task2", "Task3", "Task4", "Task5", "Task6", "Task7", "Task8", "Task9", "Task10", "Task11"]

