#include <stdbool.h>
#include <stdio.h>
#include "failure_stack.h"

void initialize_failed_stack(FAILURE_STACK *fs){
    fs->top = -1;   //for now empty
}

bool isFull(FAILURE_STACK *fs){
    return fs->top == MAX_FAILED-1;
}

bool isEmpty(FAILURE_STACK *fs){
    return fs->top == -1;   //if top==0, then there is one element
}

void push(FAILURE_STACK *fs, PROCESS_QUEUE data){
    if(isFull(fs)){
        printf("stack is full, cannot push\n");
        return;
    }
    fs->top++;
    fs->stack[fs->top] = data;
}

PROCESS_QUEUE pop(FAILURE_STACK *fs){
    if (isEmpty(fs)) {
        printf("Stack is empty, cannot pop\n");
        PROCESS_QUEUE emptyQueue;
        initialize_process_queue(&emptyQueue);
        return emptyQueue;
    }
    PROCESS_QUEUE topElement = fs->stack[fs->top];
    fs->top--;
    return topElement;
}
