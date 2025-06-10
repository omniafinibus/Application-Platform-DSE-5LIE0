# Application-Platform-DSE-5LIE0
An automation for the design exploration of a 7 dimensional design field for the course multiprocessors

## Overview

This project automates the Design Space Exploration (DSE) of a multi-processor embedded system. The system is evaluated for different architectural and task scheduling configurations with the goal of identifying energy-efficient and high-performance designs. The DSE script leverages simulation tools to analyze metrics such as energy consumption, latency, and throughput across a vast configuration space.

This work was done as part of 5LIE0 Multiprocessors and focuses on evaluating how design parameters affect system performance. Due to the sheer number of possible configurations (~10²⁷ for six nodes), the code was developed to systematically automate simulations, collect performance data, and narrow down optimal configurations with some human input.

## Why Automation?

Manual simulation of the full design space is computationally infeasible due to:
- Multiple tunable dimensions (processors, schedulers, voltage levels, priorities, mappings, graph modifications).
- Combinatorial explosion (over 10²⁷ configurations possible).
- Simulations taking up to several seconds each.

The automation:
- Enables parallelized simulation across multiple configurations.
- Applies exhaustive, iterative, and directed search techniques.
- Stores results, evaluates performance metrics, and ranks configurations.


## Key Components

### 1. Platform Configuration (`PlatformConfig`)
Encapsulates the hardware and application configuration:
- Processors (ARMv8, Adreno, MIPS)
- Schedulers (FCFS, PB)
- Voltage Scaling
- Task Mappings
- Task Priorities
- Application Graph Transformations

### 2. Simulation Interface
- `single_sim(config)` – Run one simulation.
- `parallel_sims(configs)` – Batch run multiple simulations.
- `analyze_results(config)` – Parses simulation output for energy, latency, throughput.

### 3. Exploration Algorithms
- `exhaustive_search(n)` – Full evaluation for small configurations (e.g., 1 or 2 nodes).
- `iterative_search(n, steps, breadth)` – Greedy search through configuration tree.
- `directed_iterative_search(n, steps, breadth, maxDepth)` – Depth-limited, guided search based on performance metric.

### 4. Application-Specific Evaluation
- Applies task graph transformations (e.g., merging tasks 3 and 8).
- Applies different mappings and priority assignments.
- Compares configurations using a geometric mean metric:  
  mu_geometric = (Theta/(N\*E\*L_avg))^(1/4)
  where:
  - Theta: Throughput
  - L_avg: Average Latency
  - N: Number of Nodes
  - E: Energy


## Usage Instructions

1. Set up initial configuration in `PlatformConfig`.
2. Run simulations via:
   ```python
   single_sim(config)           # Single run
   parallel_sims([config1, config2, ...])  # Batch run

3. Perform exploration:

   ```python
   exhaustive_search(n)
   iterative_search(n, steps, breadth)
   directed_iterative_search(n, steps, breadth, maxDepth)
   ```
4. Analyze and store results:

   ```python
   analyze_results(config)
   config.write_results_to_csv(output_path)
   ```

## Example: Running a Full Search

```python
# Initial setup
config = PlatformConfig(
    dMapping={...},
    dProcessors={...},
    dSchedules={...},
    dVoltageScales={...},
    dPriority={...}
)

# Run single simulation
single_sim(config)

# Analyze result
energy, latency, throughput = analyze_results(config)
```



## File Output

* Simulation logs: XML traces per processor and battery usage.
* Result CSVs: Summarized metrics stored for:

  * `original_application_transformation.csv`
  * `altered_mapping.csv`
  * `priority_based_search.csv`



## Assignment Context

The assignment explores optimization in embedded multi-core systems through Design Space Exploration (DSE). The goal is to balance performance and power efficiency by altering:

* Hardware setup (processor, scheduler, voltage)
* Task allocation and priority
* Task graph structure

This script enables evaluation of these dimensions programmatically, making DSE feasible within practical time constraints.



## Limitations

* Some configurations (e.g., with low node count) result in simulation errors due to unmet throughput constraints.
* Task graph transformations showed theoretical promise but encountered runtime issues during simulation.

