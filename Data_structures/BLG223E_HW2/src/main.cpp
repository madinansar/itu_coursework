#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "execution_functions.h"
#include "process_queue.h"


void printProcessManager(PROCESS_MANAGER *pm) {
    printf("Process Manager Details:\n");
    printf("=========================\n");

    if (isEmpty(pm)) {
        printf("The process manager is empty.\n");
        printf("=========================\n");
        return;
    }

    printf("Number of Queues: %d\n", pm->size);

    // Traverse the deque
    for (int i = 0; i < pm->size; i++) {
        int queueIndex = (pm->front + i) % MAX_PROCESS;
        PROCESS_QUEUE *currentQueue = &pm->deque[queueIndex];

        printf("\nQueue %d Details:\n", i + 1);
        printf("Size: %d\n", currentQueue->size);

        if (isEmpty(currentQueue)) {
            printf("  This queue is empty.\n");
        } else {
            printf("Processes:\n");
            PROCESS_QUEUE tempQueue = *currentQueue;  // Use a temporary queue to dequeue for printing
            while (!isEmpty(&tempQueue)) {
                PROCESS process = dequeue(&tempQueue);
                printf("  Process ID: %d, Priority: %d\n", process.pid, process.priority);
            }
        }
    }

    printf("=========================\n");
}

void printInsertionQueue(INSERTION_QUEUE *eq) {
    printf("Insertion Queue Details:\n");
    printf("=========================\n");

    if (isEmpty(eq)) {
        printf("The insertion queue is empty.\n");
        printf("=========================\n");
        return;
    }

    printf("Number of Queues: %d\n", eq->size);

    // Traverse the queue
    for (int i = 0; i < eq->size; i++) {
        int queueIndex = (eq->front + i) % MAX_OPERATION;
        PROCESS_QUEUE *currentQueue = &eq->queue[queueIndex];

        printf("\nQueue %d Details:\n", i + 1);
        printf("  Iteration: %d\n", currentQueue->iteration);
        printf("  Size: %d\n", currentQueue->size);

        if (isEmpty(currentQueue)) {
            printf("  This queue is empty.\n");
        } else {
            printf("  Processes:\n");
            for (int j = 0; j < currentQueue->size; j++) {
                PROCESS process = currentQueue->queue[j];
                printf("    Process ID: %d, Priority: %d\n", process.pid, process.priority);
            }
        }
    }

    printf("=========================\n");
}
void printFailureStack(FAILURE_STACK *fs) {
    printf("Failure Stack Details:\n");
    printf("=========================\n");

    if (fs->top == -1) { // Check if the stack is empty
        printf("The failure stack is empty.\n");
        printf("=========================\n");
        return;
    }

    // Traverse the stack
    for (int i = fs->top; i >= 0; i--) {
        PROCESS_QUEUE *currentQueue = &fs->stack[i];
        printf("\nQueue %d Details (from stack index %d):\n", fs->top - i + 1, i);
        printf("  Size: %d\n", currentQueue->size);

        if (isEmpty(currentQueue)) {
            printf("  This queue is empty.\n");
        } else {
            printf("  Processes:\n");
            for (int j = 0; j < currentQueue->size; j++) {
                PROCESS process = currentQueue->queue[j];
                printf("    Process ID: %d, Priority: %d\n", process.pid, process.priority);
            }
        }
    }

    printf("=========================\n");
}



int main() {
    
    PROCESS_MANAGER pm;
    initialize_process_manager(&pm);
    const char *filename = "initial_processes.txt";

    INSERTION_QUEUE eq;
    initialize_execution_queue(&eq);
    const char *filename_iq = "arriving_processes.txt";

    read_process_file(filename, &pm);
    printf("pm's size is %d \n", pm.size);
    //printProcessManager(&pm);

    read_insertion_file(filename_iq, &eq);
    //printInsertionQueue(&eq);

    FAILURE_STACK fs;
    initialize_failed_stack(&fs);

    

    execution_loop(&pm, &eq, &fs);

    printFailureStack(&fs);

    return 0;
}

