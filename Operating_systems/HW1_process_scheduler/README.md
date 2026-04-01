
Computer Operating Systems - Homework Assignment - Process Scheduler
Done by Madina Alzhanova 150220939

This homwork implements a simple user-level process scheduler in C using `fork`, `execlp`, `SIGSTOP`, `SIGCONT`, and `waitpid`.

## Topic and Task

The task is to read jobs from an input file and schedule them with time slicing and priority-aware selection. The scheduler logs process lifecycle events (create, stop, resume, finish) into a log file.

## Entities

- `scheduler.c`: main scheduler logic.
- `jobs.txt`: input job definitions (`TimeSlice`, arrival time, priority, execution time).
- `scheduler.log`: runtime event log.
- `Makefile`: build and run commands.
- `HW1 Description.pdf`: assignment description.
- `report.pdf`: homework report.

## Workflow

1. Parse `jobs.txt` and initialize job table.
2. At each time step, choose next arrived job by priority (with tie handling).
3. Start or resume selected process, run for one time slice, then stop or finalize.
4. Repeat until all jobs complete, while writing events to `scheduler.log`.

## Demo

![Demo](./screen_recording.gif)

To compile and run the program use makefile:

```bash
make
make run
```

or compile manually:

```bash
gcc scheduler.c -o scheduler
./scheduler
```