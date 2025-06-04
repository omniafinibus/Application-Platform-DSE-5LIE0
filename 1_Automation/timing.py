from constants import L_TASKS
from dataclasses import dataclass, field

# =====================
# Timing Measurement Dataclasses
# =====================
    
@dataclass
class TaskTiming:
    """
    Stores timing information for a specific task execution.
    """
    name: str = None  # Task name
    start: float = float('inf')  # Start time
    stop: float = 0.0  # Stop time
    down: float = 0.0  # Time spent in an idle state (interruption time)
    iteration: int = None  # Iteration number of execution
    
@dataclass
class IterationTiming:
    """
    Stores task timing for a specific iteration of execution.
    """
    _dTasks: dict  # Dictionary to store task timing per iteration
    _latency: float = float('inf')  # Iteration latency
    
    def add_measurment(self, task: TaskTiming):
        """
        Adds task timing to iteration tracking.
        """
        if task.name not in self._dTasks.keys():
            message = (f"Task {task.name} not found in IterationTiming")
            # print(message)
            # raise Exception(message)
        
        self._dTasks[task.name] = task
        
    def get_latency(self):
        """
        Calculates the latency for the iteration.
        Returns:
            float: Computed latency.
        """
        self._latency = self._dTasks[L_TASKS[-1]].stop - self._dTasks[L_TASKS[0]].start
        if self._latency <= 0:
            # message = (f"Iteration timing has an incorrect latency {self._latency}")
            # print(message)
            # raise Exception(message)
            return 0.0
        else:
            return self._latency
    
@dataclass
class TimingMeasurements:
    """
    Stores and processes timing metrics over multiple iterations.
    """
    _avgLatency: float = 0.0  # Average latency across iterations
    _dIterations: dict = field(default_factory=dict)  # Dictionary of iteration timings
    _throughput: float = 0.0  # System throughput
    startTime: float = float('inf')  # Start time of first iteration
    stopTime: float = 0.0  # Stop time of last iteration
    
    def add_measurement(self, task: TaskTiming):
        """
        Adds a new task timing measurement to the corresponding iteration.
        
        Args:
            task (TaskTiming): Task timing information.
        """
        if int(task.iteration) not in self._dIterations.keys():
            # Create a new IterationTiming instance for this iteration if not already present
            self._dIterations[task.iteration] = IterationTiming({taskName: TaskTiming() for taskName in L_TASKS})
        
        # Add task timing information to the iteration tracking
        self._dIterations[task.iteration].add_measurment(task)
        
        # Update the overall simulation start and stop times
        self.startTime = min(float(task.start), self.startTime)
        self.stopTime = max(float(task.stop), self.stopTime)

    def get_avg_latency(self):
        """
        Computes the average latency across all valid iterations.
        
        Returns:
            float: The computed average latency.
        """
        # Count the number of incomplete iterations (latency = 0)
        numOfIncompleteIt = len(list(filter(lambda x: x == 0.0, [it.get_latency() for it in self._dIterations.values()])))
        numOfValidIt = len(self._dIterations) - numOfIncompleteIt

        # Compute average latency for valid iterations
        self._avgLatency = 0.0 if numOfValidIt == 0 else sum([iteration.get_latency() for iteration in self._dIterations.values()]) / numOfValidIt
        return self._avgLatency
                
    def get_throughput(self):
        """
        Computes the system throughput as the number of completed iterations per unit time.
        
        Returns:
            float: The computed throughput.
        """
        # Ensure the simulation period is valid before computing throughput
        self._throughput = len(self._dIterations) / (self.stopTime - self.startTime) if (self.stopTime - self.startTime) > 0 else 0.0
        return self._throughput
        