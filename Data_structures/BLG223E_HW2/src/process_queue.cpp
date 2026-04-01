#include <stdbool.h>
#include <stdio.h>
#include "process_queue.h"

void initialize_process_queue(PROCESS_QUEUE *pq){
    for(int i = 0; i< QUEUE_SIZE; i++){
        pq->queue[i].pid = -1;
        pq->queue[i].priority = -1;
    }
    pq->front = 0;
    pq->rear = -1; //for now
    pq->size = 0;
    pq->priority = -1;  //default for now
    pq->iteration = -1;
}

bool isFull(PROCESS_QUEUE *pq){
    return pq->size == QUEUE_SIZE;
}

bool isEmpty(PROCESS_QUEUE *pq){
    return pq->size == 0;
}

PROCESS peek(PROCESS_QUEUE *pq){
    if(isEmpty(pq)){
        printf("empty, cannot peek");
        PROCESS emptyProcess = { -1, -1 };
        return emptyProcess; 
    }
    return pq->queue[pq->front];
}

void enqueue(PROCESS_QUEUE *pq, PROCESS data){
    if(isFull(pq)){
        printf("queue is full, cannot enqueue");
        return;
    }
    pq->rear = (pq->rear + 1) % QUEUE_SIZE; //incremnet first, then add bc rear points to the last element
    pq->queue[pq->rear] = data;
    pq->size++;
}

PROCESS dequeue(PROCESS_QUEUE *pq){
    if(isEmpty(pq)){
        printf("queue is empty, cannot dequeue");
        PROCESS emptyProcess = { -1, -1 };
        return emptyProcess; 
    }
    PROCESS data = pq->queue[pq->front];
    pq->front = (pq->front + 1) % QUEUE_SIZE;
    pq->size--;
    return data;
}

