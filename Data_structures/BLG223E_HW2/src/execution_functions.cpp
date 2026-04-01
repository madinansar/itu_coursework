#include <stdbool.h>
#include <stdio.h>
#include "execution_functions.h"
#include "process_queue.h"

void read_process_file(const char *filename, PROCESS_MANAGER *pm){
     FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open file");
        return;
    }

    char line[256];
    int pid, priority, isHead;

    PROCESS_QUEUE currentQueue;
    initialize_process_queue(&currentQueue);

    while(fgets(line, sizeof(line), file)){
        if(sscanf(line, "%d, %d, %d", &pid, &priority, &isHead) == 3){
            PROCESS process;
            process.pid = pid;
            process.priority = priority;
            //process.isHead = isHead;
            

            enqueue(&currentQueue, process);
            if (isHead == 1) { 
                    if (currentQueue.queue[0].priority == 1) {
                        insert_front(pm, currentQueue); 
                    } else {
                        insert_rear(pm, currentQueue); 
                    }
            initialize_process_queue(&currentQueue);
            }

        }
    }

    if (currentQueue.size > 0) {
        if (currentQueue.queue[0].priority == 1) {
            insert_front(pm, currentQueue); // High-priority queue
        } else {
            insert_rear(pm, currentQueue); // Low-priority queue
        }
    }

    fclose(file);
}



void read_insertion_file(const char *filename, INSERTION_QUEUE *eq){
     FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open file");
        return;
    }

    char line[256];
    int iteration, pid, priority, isHead;

    PROCESS_QUEUE currentQueue;
    initialize_process_queue(&currentQueue);

    while (fgets(line, sizeof(line), file)) {
        if (sscanf(line, "%d, %d, %d, %d", &iteration, &pid, &priority, &isHead) == 4) {
            PROCESS process;
            process.pid = pid;
            process.priority = priority;
            currentQueue.iteration = iteration; 

            enqueue(&currentQueue, process); // Add process to the current queue

            if (isHead == 1) { 
                enqueue(eq, currentQueue); 
                //printf("enqueued succesfully");
                initialize_process_queue(&currentQueue); 
                
            }
        }
    }

    if (currentQueue.size > 0) {
        enqueue(eq, currentQueue);
    }
    fclose(file);
}


void execution_loop(PROCESS_MANAGER *pm, INSERTION_QUEUE *eq, FAILURE_STACK *fs){
    int iter = -1;

    FILE *file = fopen("execution_run.txt", "w");
    if(file == NULL){
        printf("File not found\n");
        return;
    }



     while(pm->size!=0){
        char status = 's';
        PROCESS_QUEUE currentQueue;
        initialize_process_queue(&currentQueue);
        currentQueue = delete_front(pm);

        PROCESS_QUEUE tempQueue;
        tempQueue = currentQueue;

        while(!isEmpty(&currentQueue)){
            status = 's';
            
            PROCESS currentProcess;

            initialize_process(&currentProcess, currentQueue.queue->pid, currentQueue.queue->priority);
            currentProcess = dequeue(&currentQueue);
            iter++;

            if(eq->size>0 && iter+1 == eq->queue[eq->front].iteration){
                PROCESS_QUEUE arrivingQueue = dequeue(eq);
                if(arrivingQueue.queue->priority == 1){
                    insert_front(pm, arrivingQueue);
                    printf("inserted front");
                } else {
                    insert_rear(pm, arrivingQueue);
                    printf("inserted back");
                }
            } 

            if(currentProcess.pid % 8 == 0){
                status = 'f';
                fprintf(file, "%d, %c\n", currentProcess.pid, status);
                printf("Process ID %d failed. Remaining queue pushed to failure stack.\n", currentProcess.pid);
                push(fs, tempQueue);
                initialize_process_queue(&currentQueue);
                initialize_process_queue(&tempQueue);
                break;
            }
            
            fprintf(file, "%d, %c\n", currentProcess.pid, status);
            printf("Executing Process ID: %d, Status: %c, Priority: %d (Iteration: %d)\n", currentProcess.pid, status, currentProcess.priority, iter);


        }
    

    }

    
}
