#include <stdbool.h>
#include <stdio.h>
#include "process_manager.h"

void initialize_process_manager(PROCESS_MANAGER *pm){
    for(int i = 0; i<MAX_PROCESS; i++){
        initialize_process_queue(&pm->deque[i]);
    }
    pm->front = 0;
    pm->rear = -1;
    pm->size = 0;
}

bool isFull(PROCESS_MANAGER *pm){
    return pm->size == MAX_PROCESS;
}

bool isEmpty(PROCESS_MANAGER *pm){
    return pm->size == 0;
}

void insert_front(PROCESS_MANAGER *pm, PROCESS_QUEUE pq){
    if(isFull(pm)){
            printf("deque is full, cannot insert_rear\n");
            return;
    }

    pm->front = (pm->front - 1 + MAX_PROCESS) % MAX_PROCESS;
    pm->deque[pm->front] = pq;
    pm->size++;
}

void insert_rear(PROCESS_MANAGER *pm, PROCESS_QUEUE pq){
    if(isFull(pm)){
        printf("deque is full, cannot insert_rear\n");
        return;
    }
    pm->rear = (pm->rear+1)%MAX_PROCESS;
    pm->deque[pm->rear] = pq;
    pm->size++;

}

PROCESS_QUEUE delete_front(PROCESS_MANAGER *pm){
    if(isEmpty(pm)){
        printf("pm is empty, cannot delete from front\n");
        PROCESS_QUEUE emptyQueue = { {-1}, -1, -1, -1, -1, -1 };
        return emptyQueue;
    }
    PROCESS_QUEUE pq = pm->deque[pm->front];
    pm->front = (pm->front+1)%MAX_PROCESS;
    pm->size--;
    return pq;
}

PROCESS_QUEUE delete_rear(PROCESS_MANAGER *pm){
    if(isEmpty(pm)){
        printf("pm is empty, cannot delete from front\n");
        PROCESS_QUEUE emptyQueue = { {-1}, -1, -1, -1, -1, -1 }; //PROCESS_QUEUE emptyQueue = { { {-1} }, -1, -1, -1, -1, -1 };

        return emptyQueue;
    }
    
    PROCESS_QUEUE deletedQueue = pm->deque[pm->rear];
    pm->rear = (pm->rear - 1 + MAX_PROCESS) % MAX_PROCESS;

    pm->size--;
    return deletedQueue;
}

