# Selective Repeat ARQ Simulator (C/C++ Optimized)

This folder contains a high-performance implementation of a Selective Repeat ARQ network simulation (written in C++17 for speed, with a C-style systems pipeline) over a Gilbert-Elliott burst-error channel.

## Aim of the Project

The goal of the project is to study how protocol-level reliability mechanisms behave under realistic, bursty channel errors, and to improve throughput efficiency through implementation-level optimization.

In particular, this version focuses on:

- Fast event-driven simulation in native code.
- Selective Repeat retransmission behavior under channel state changes.
- Adaptive retransmission timeout (RTO) estimation (Jacobson/Karels + Karn's rule) to improve completion time and goodput.

## Pipeline

The simulation follows this end-to-end pipeline:

1. Generate application data and split it into transport segments.
2. Sender frames data and transmits while respecting window size W.
3. Channel applies Gilbert-Elliott state transitions and frame corruption.
4. Receiver accepts in-order frames, buffers out-of-order frames, and sends ACKs.
5. Sender processes ACKs, updates RTT/RTO, and retransmits timed-out frames.
6. Event queue advances simulated time until transfer completion or time limit.
7. Metrics are written to CSV and visualized as a goodput heatmap.

## Project Structure

- `main.cpp`: Core event-driven simulator, parallel sweep runner, CSV output.
- `classes.hpp`: Transport segment and link-frame data structures.
- `channel.hpp`: Gilbert-Elliott channel model and corruption decision logic.
- `receiver.hpp`: Selective Repeat receiver (buffering + cumulative delivery behavior).
- `sender.hpp`: Sender implementation with adaptive RTT/RTO logic (used by current build).
- `sender_improved.hpp`: Alternative/experimental sender variant.
- `plot_results.py`: Builds a goodput heatmap from simulation CSV.
- `Makefile`: Build rules (`-O3`, `-std=c++17`, `-pthread`).
- `results_baseline.csv`: Baseline run metrics.
- `results_improved_final.csv`: Optimized run metrics.
- `simulation_results_optimized_512_64.csv`: Current focused run output.
- `goodput_heatmap.png`: Goodput heatmap figure.

## Build and Run

Build the simulator:

```bash
make
```

Run:

```bash
./simulation
```

Generate heatmap from CSV:

```bash
python3 plot_results.py
```

## Result Metrics

The result files store the following columns (naming differs slightly by file):

- Window size `W`
- Payload/frame size `L`
- Random seed / run id
- Goodput (Mbps)
- Number of retransmissions
- Runtime / duration (seconds)
- Optional diagnostics: average RTT, utilization, bad-state fraction, buffer events

## Results and Interpretation

For the optimized configuration (`W=64`, `L=512`, 10 seeds):

- Mean goodput (optimized): `2.086 Mbps`
- Mean goodput (baseline): `0.890 Mbps`
- Relative goodput gain: about `+134%`
- Mean duration (optimized): `402.092 s`
- Mean duration (baseline): `942.835 s`
- Runtime reduction: about `57%`

The retransmission count remains of similar magnitude between baseline and optimized runs, but adaptive timeout control significantly reduces idle/wait time and improves effective data delivery rate.

### Goodput Heatmap

![Simulated Goodput Heatmap](/Users/madinaalzhanova/Desktop/itu_coursework/Computer_communcations/assignment2_arq_sim/goodput_heatmap.png)

The heatmap shows the expected Selective Repeat trend:

- Larger windows generally improve pipeline utilization.
- Mid-sized payloads (around 512 bytes in this setup) provide the best goodput.
- Very large payloads become more vulnerable to corruption and retransmission cost in a bursty channel.

## Notes

- Current `main.cpp` is configured for a focused benchmark (`W=64`, `L=512`).
- For full sweeps, expand the `W_VALUES` and `L_VALUES` vectors in `main.cpp`.
