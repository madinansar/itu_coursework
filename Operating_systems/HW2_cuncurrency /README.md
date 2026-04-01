# Operating Systems HW2 - Concurrency Market Simulator

## Task

This homework implements a multithreaded market simulation in C. The task is to process concurrent customer reservation/purchase requests while preserving correct stock updates and payment limits using synchronization primitives.

## Entities

- `150220939_market_sim.c`: main implementation (threads, mutexes, condition variables, logging).
- `market_sim.h`: shared constants, data structures, and function declarations.
- `input.txt`: simulation configuration and grouped customer requests.
- `log.txt`: execution log with timestamped thread actions.
- `makefile`: build rules for `market_sim`.
- `Homework2_Description.pdf`: assignment description.
- `150220939_Madina_Alzhanova_report.pdf`: report.

## Workflow

1. Read config and requests from `input.txt`.
2. Create request threads in groups; each thread tries to reserve product stock.
3. If reservation succeeds, thread waits for payment slot (`max_concurrent_payments`) before purchase.
4. On timeout or cancellation, reserved stock is returned and waiting threads are signaled.
5. All actions are logged to `log.txt` and the program exits after joining all threads.

## Run

```bash
make
./market_sim
```