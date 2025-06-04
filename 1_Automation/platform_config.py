import os
import re
from power import PowerMeasurements
from timing import TaskTiming, TimingMeasurements
from constants import MODEL_TEMPLATE, SIM_TIME, OUTPUT_DIR_BASE

# =====================
# Platform Configuration class
# =====================

def get_geometric_mean(*lInputs):
    result = 1
    for input in lInputs:
        result *= input
    return result ** (1 / len(lInputs))
    
class PlatformConfig:
    """ 
    Represents a platform configuration for design space exploration.
    
    Attributes:
        dMapping (dict): Task-to-processor dMapping.
        dPriority (dict): Task priorities.
        dProcessors (dict): Processor types for each node.
        dSchedules (dict): Scheduling policies for each processor.
        dVoltageScales (dict): Voltage scaling factors.
        iteration (int): Iteration number for configuration identification.
        configName (str): Name of the configuration.
        outputDir (Path): Directory where results will be stored.
    """

    def __init__(self, dMapping: dict, dPriority: dict, dProcessors: dict, 
                 dSchedules: dict, dVoltageScales: dict, iteration: int = 0, configName: str = None):
        self.applicationType = "application"
        self.iteration = iteration
        self.numOfNodes = len(dProcessors)  # Number of processing nodes in the configuration
        self.dMapping = dMapping
        self.dPriority = dPriority
        self.dProcessors = dProcessors
        self.dSchedules = dSchedules
        self.dVoltageScales = dVoltageScales
        self._measPower = PowerMeasurements()  # Initialize power measurement tracking
        self._measTiming = TimingMeasurements()  # Initialize timing measurement tracking
        self._get_name()
        if configName is not None:
            self.configName = configName
      
    def _get_name(self):
        lProc = [val[1] for val in sorted([(name, value) for name, value in  self.dProcessors.items()], key=lambda x : x[0])]
        lSched = [val[1] for val in sorted([(name, value) for name, value in  self.dSchedules.items()], key=lambda x : x[0])]
        lVolt = [val[1] for val in sorted([(name, value) for name, value in  self.dVoltageScales.items()], key=lambda x : x[0])]
        self.configName  = f"N{self.numOfNodes}"
        self.configName += f"-P" + "_".join([proc[0:2] for proc in lProc])
        self.configName += f"-S" + "_".join([sched[0:2] for sched in lSched])
        self.configName += f"-V" + "_".join([str(int(100*float(volt.split('/')[0])/float(volt.split('/')[1]))) for volt in lVolt])
        self.get_output_dir()
      
    def get_output_dir(self):
        lMap = ["T" + "".join(re.findall(r'[0-9]', name)) + "-N" + "".join(re.findall(r'[0-9]', value)) for name, value in  self.dMapping.items()]
        lPri = ["T" + "".join(re.findall(r'[0-9]', name)) + "-P" + "".join(re.findall(r'[0-9]', value)) for name, value in  self.dPriority.items()]
        lProc = [val[1] for val in sorted([(name, value) for name, value in  self.dProcessors.items()], key=lambda x : x[0])]
        lSched = [val[1] for val in sorted([(name, value) for name, value in  self.dSchedules.items()], key=lambda x : x[0])]
        lVolt = [val[1] for val in sorted([(name, value) for name, value in  self.dVoltageScales.items()], key=lambda x : x[0])]
        
        self.outputDir = OUTPUT_DIR_BASE.joinpath(
            f"{self.numOfNodes}Nodes",
            f"Map" + "_".join(lMap),
            f"Pri" + "_".join(lPri),
            f"Pro" + "_".join([proc[0:2] for proc in lProc]),
            f"Sched" + "_".join([sched[0:2] for sched in lSched]),
            f"Volt" + "_".join([str(int(100*float(volt.split('/')[0])/float(volt.split('/')[1]))) for volt in lVolt])
        )
        
        return self.outputDir
      
    def get_model(self):
        """ 
        Generates a simulation model based on the configuration parameters.
        
        Returns:
            str: The formatted model string with parameters filled in.
        """
        return MODEL_TEMPLATE.format(params={
            "application":         self.applicationType,
            "numOfNodes":          str(len(self.dProcessors)),
            "simTime":             SIM_TIME,
            "mapping":             "".join([f"\t\t{label} := \"{value}\",\n" for label, value in self.dMapping.items()]),
            "processorAssignment": "".join([f"\t\t{label} := \"{value}\",\n" for label, value in self.dProcessors.items()]),
            "scheduleAssignment":  "".join([f"\t\t{label} := \"{value}\",\n" for label, value in self.dSchedules.items()]),
            "priorityAssignment":  "".join([f"\t\t{label} := {value},\n"     for label, value in self.dPriority.items()]),
            "voltageScaling":      "".join([f"\t\t{label} := {value},\n"     for label, value in self.dVoltageScales.items()]),
            "channels":            "\t{ Application.Buffers, MPSoC.CommunicationResources }\n\t{ Application.Tasks, MPSoC.ComputationResources }\n"
        })

    def add_timing_meas(self, task: TaskTiming):
        """
        Adds task timing measurement data to the configuration.
        
        Args:
            task (TaskTiming): Task timing information.
        """
        self._measTiming.add_measurement(task)
        
    def get_metrics(self):
        """
        Retrieves system performance metrics including power, energy, latency, and throughput.
        
        Returns:
            tuple: (power trace, total energy, average latency, throughput)
        """
        return self._measPower.get_energy(), self._measTiming.get_avg_latency(), self._measTiming.get_throughput()
    
    def set_iteration(self, iteration):
        self.iteration = iteration
    
    def write_results_to_csv(self, file):
        if os.path.isfile(file):
            f = open(file, "a")
        else:
            f = open(file, "w")
            f.write(f"&;")
            f.write("\\rot\{Geometric Mean\}&;")
            f.write("\\rot\{Nodes\}&;")
            f.write("\\rot\{Energy\}&;")
            f.write("\\rot\{Average Latency\}&;")
            f.write("\\rot\{Throughput\}&;")
            f.write("\\rot\{Iteration\}&;")
            for i in range(1,7):
                f.write("\\multicolumn\{3\}\{|c||\}\{" + f"Node {i}" + "\}")
                
            for i in range(1,12):
                f.write("\\multicolumn\{2\}\{|c||\}\{" + f"Task {i}" + "\}")
                
            f.write("\\\\\n")
            
            f.write("&;")
            f.write("&;")
            f.write("&;")
            f.write("&;")
            f.write("&;")
            f.write("&;")
            f.write("&;")
            for i in range(1,7):
                f.write("\\rot\{Processor\}&;")
                f.write("\\rot\{Schedule\}&;")
                f.write("\\rot\{Voltage [\%]\}&;")
                
            for i in range(1,12):
                f.write("\\rot\{Node\}&;")
                f.write("\\rot\{Priority\}&;")
                
            f.write("\\\\\n")

        f.write(f"&;")
        f.write(f"{get_geometric_mean(1/self.numOfNodes, 1/self._measPower.get_energy(), 1/self._measTiming.get_avg_latency(), self._measTiming.get_throughput())}&;")
        f.write(f"{self.numOfNodes}&;")
        f.write(f"{self._measPower.get_energy()}&;")
        f.write(f"{self._measTiming.get_avg_latency()}&;")
        f.write(f"{self._measTiming.get_throughput()}&;")
        f.write(f"{self.iteration}&;")
        for i in range(1,self.numOfNodes+1):
            processor = self.dProcessors[f"Node{i}ProcessorType"]
            f.write(f"{processor}&;")
            schedules = self.dSchedules[f"OSPolicy{i}"]
            f.write(f"{schedules}&;")
            voltageScales = self.dVoltageScales[f"VSF{i}"]
            f.write(f"{voltageScales}&;")
            
        if self.numOfNodes < 7:
            f.write(f"&;")
            f.write(f"&;")
            f.write(f"&;")
            
        for i in range(1,12):
            mapping = self.dMapping[f"MapTask{i}To"]
            f.write(f"{mapping}&;")
            priority = self.dPriority[f"PriorityTask{i}"]
            f.write(f"{priority}&;")
        
        f.write("\\\\\n")
                    
        f.close()
