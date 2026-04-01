# C++ Simulation
This directory contains the high-performance C++ implementation of the Selective Repeat ARQ protocol simulation over a Gilbert-Elliot channel.

## Files
- `main.cpp`: Main simulation loop (parameters sweep).
- `channel.hpp`: Gilbert-Elliot channel model.
- `sender.hpp`: Selective Repeat Sender logic.
- `sender_improved.hpp`: Selective Repeat Sender logic (with adaptive RTO).
- `receiver.hpp`: Selective Repeat Receiver logic.
- `classes.hpp`: Shared data structures (Frame, Packet).
- `Makefile`: Build configuration.
- `plot_results.py`: Python script to visualization results.

## Compilation
To build the simulation, run:
```bash
make
```
This produces the `simulation` executable. If u want to run full simulation, makefile should be chnaged and main_orginal.cpp and sender.hpp should be used.

## Running
Execute the simulation:
```bash
./simulation
```
It will run a parameter sweep over:
- Window Sizes (W): 2, 4, 8, 16, 32, 64
- Frame Sizes (L): 128, 256, 512, 1024, 2048, 4096
- Seeds: 0-9

Progress will be printed to stdout.

## Results
The simulation generates `simulation_results.csv` with columns:
- W, L, Seed
- Goodput_Mbps
- Retransmissions
- Duration_Sec
- BadStateFraction

## Visualization
To generate a heatmap of Goodput vs W and L:
```bash
python3 plot_results.py
```
This requires `pandas`, `seaborn`, and `matplotlib`.
