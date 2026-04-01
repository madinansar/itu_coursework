#include "exam.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Function to create a new exam and link it properly in the day
struct Exam* CreateExam(int startTime, int endTime, const char* courseCode) {
    Exam* newExam = (Exam*)malloc(sizeof(Exam));
    if (!newExam) {
        fprintf(stderr, "Memory allocation failed!\n");
        exit(EXIT_FAILURE); // Exit if memory allocation fails
    }
    newExam->startTime = startTime;
    newExam->endTime = endTime;
    strncpy(newExam->courseCode, courseCode, sizeof(newExam->courseCode)-1);    // 0 1 2 3 x
    newExam->courseCode[sizeof(newExam->courseCode)-1] = '\0';
    newExam->next = NULL;   //for the first element

    //printf("Exam is created!");
    return newExam;
}

void PrintExam(Exam* exam) {
    if (exam == NULL) {
        printf("Exam is NULL.\n");
        return;
    }
    printf("Exam Details:\n");
    printf("Course Code: %s\n", exam->courseCode);
    printf("Start Time: %d\n", exam->startTime);
    printf("End Time: %d\n", exam->endTime);
}