from constants import SIM_TIME
from dataclasses import dataclass, field


# =====================
# Power Measurement Dataclass
# =====================

@dataclass
class PowerMeasurements:
    """
    Stores power usage information during simulation, tracking energy consumption over time.
    """
    _dDifference: dict = field(default_factory=dict)  # Stores power difference at different times
    _ltPower: list = field(default_factory=list)  # List of power readings over time
    _energy: float = 0.0  # Total energy consumption
    startTime: float = float('inf')  # Earliest recorded time
    stopTime: float = 0.0  # Latest recorded time
    
    def update_ltPower(self, difference, time):
        """
        Updates power consumption data.
        Args:
            difference (float): Power difference at a given time.
            time (float): The time at which power change occurs.
        """
        if float(time) not in self._dDifference.keys():
            self._dDifference[float(time)] = float(difference)
        else:
            self._dDifference[float(time)] += float(difference)
            
        self.startTime = min(float(time), self.startTime)
        self.stopTime = max(float(time), self.stopTime)
        
    def get_ltPower_trace(self):
        """
        Generates a power trace (time vs. power).
        Returns:
            list: Power measurements over time.
        """
        lTrace = sorted([(time, difference) for time, difference in self._dDifference.items()], key=lambda diff: diff[0])
        
        self._ltPower = []
        self._ltPower.append((0.0, 0.0))  # Initial power at time 0
        for i in range(0, len(lTrace)):
            self._ltPower.append((lTrace[i][0], self._ltPower[i][1] + lTrace[i][1]))
        
        self._ltPower.sort(key=lambda x: x[0])
        
        return self._ltPower
        
    def get_energy(self):
        """
        Computes total energy consumption over the simulation period.
        Returns:
            float: Total energy usage.
        """
        power = self.get_ltPower_trace()
        
        self._energy = 0.0
        if len(power):
            for i in range(len(power)-2):
                self._energy += power[i][1] * (power[i+1][0] - power[i][0])
                if self._energy < 0:
                    raise Exception(f"Improbable energy consumption {self._energy} between {power[i][0]} and {power[i+1][0]} mininum power is {min([time[1] for time in power])}")
                
                if float(SIM_TIME) > power[-1][0]:
                    self._energy += power[-1][1] * (float(SIM_TIME) - power[-1][0])
                
        
        if self._energy < 0:
            raise Exception(f"Improbable energy consumption  {self._energy} mininum power is {min([time[1] for time in power])}")
        
        return self._energy