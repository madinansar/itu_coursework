This project simulates a market environment using multithreading in C. Customers attempt to reserve products concurrently, and synchronization mechanisms are used to handle stock availability and avoid race conditions.

Files:
150220939_market_sim.c - main file containing all logic 
market_sim.h - header file
makefile - builds the project
log.txt - logging  market simulation
input.txt - given configs
report.pdf - answers to questions, design decisions

How to Run using Makefile:
Compile: make
Run: ./market_sim

How to Run using gcc:
Compile: gcc 150220939_market_sim.c -o sim
Run: ./sim