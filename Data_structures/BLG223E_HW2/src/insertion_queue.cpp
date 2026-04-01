#include <stdbool.h>
#include <stdio.h>
#include "insertion_queue.h"

void initialize_execution_queue(INSERTION_QUEUE *iq){
    for(int i = 0; i<MAX_OPERATION; i++){
         initialize_process_queue(&iq->queue[i]);
    }
    iq->front = 0;
    iq->rear = -1;
    iq->size = 0;
}

bool isFull(INSERTION_QUEUE *iq){
    return iq->size == MAX_OPERATION;
}

bool isEmpty(INSERTION_QUEUE *iq){
    return iq->size == 0;
}

PROCESS_QUEUE peek(INSERTION_QUEUE *iq){
    if(isEmpty(iq)){
        printf("empty, cannot peek");
        PROCESS_QUEUE emptyProcessQueue = {{-1}, -1, -1, -1, -1};
        return emptyProcessQueue; 
    }
    return iq->queue[iq->front];
}

void enqueue(INSERTION_QUEUE *iq, PROCESS_QUEUE data){
    if(isFull(iq)){
        printf("queue is full, cannot enqueue");
        return;
    }
    iq->rear = (iq->rear + 1) % MAX_OPERATION;
    iq->queue[iq->rear] = data;
    iq->size++;
}

PROCESS_QUEUE dequeue(INSERTION_QUEUE *iq){
    if (isEmpty(iq)) {
        printf("queue is empty, cannot dequeue\n");
        PROCESS_QUEUE emptyQueue = { { {-1} }, -1, -1, -1, -1, -1 };
        return emptyQueue;
    }

    PROCESS_QUEUE data = iq->queue[iq->front];
    iq->front = (iq->front + 1) % MAX_OPERATION; 
    return data;
}