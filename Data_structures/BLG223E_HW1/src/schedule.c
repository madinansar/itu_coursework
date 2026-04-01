#include "schedule.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char globCourseCode[50];    //global courseCode string: Remove function also "returns" courseCode, while its return type is int
int globUpdFlag = 0; //0 for Add, 1 for Upd

// Create a new schedule with 7 days
struct Schedule* CreateSchedule() {

    Schedule* schedule = (Schedule*)malloc(sizeof(Schedule));
    schedule->head = NULL;


    const char* namesOfDays[] = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"};

    Day* prevDay = NULL;    //pointer to traverse
    
    for(int i =0; i<7; i++){
        Day* newDay = (Day*)malloc(sizeof(Day));
        strcpy(newDay->dayName, namesOfDays[i]);    //C style
        newDay->examList = NULL;    //initially empty

        if(schedule->head == NULL){ //no days added no sch yet
            schedule->head = newDay;    //monday in 1st iter
        }
        else{
            prevDay->nextDay = newDay;
        }
        prevDay = newDay;
        //printf("day no: %d\n", i);
    }   //end for
    prevDay->nextDay = schedule->head;  //making it circular
    printf("Schedule creation complete.\n");

    return schedule;
}


// Add an exam to a day in the schedule
int AddExamToSchedule(struct Schedule* schedule, const char* day, int startTime, int endTime, const char* courseCode) {
   
    int targetIndex = 0;

    if(startTime < 8 || startTime>17 || endTime<9 || endTime>20 || endTime-startTime>3){
        printf("Invalid exam.\n");
        return 3;   
    }

//find targetDay
    Day* targetDay = schedule->head;    //start from monday
    int found = 0;
    for(int i =0; i<7; i++){
        if(strcmp(targetDay->dayName, day)==0){
            found =1;
            targetIndex = i;
            break;
        }
        targetDay = targetDay->nextDay;
    }
    if (!found) {
        printf("Error: Day %s not found in schedule.\n", day);
        return -1; // Return or handle error if the day isn't found
    }
    
    int examAdded =0; //check if successfully added
    int count =0; //to check < 7 days count should check for count < daysRemaining
    int firstTry = 1;   //true by default, becomes false in second+ try
    int daysRemaining = 7 - targetIndex;

    while(count<daysRemaining && examAdded==0){
        Exam* currentExam = targetDay->examList;    //for traversing
        Exam* prev = NULL;  //prev exam, for finish time


        while(currentExam != NULL && currentExam->startTime<startTime){

            prev = currentExam;     //traverse traverse
            currentExam = currentExam->next; 
        }
    

        // Check for time conflict with both previous and current exams
        if((prev == NULL && currentExam == NULL) || (prev == NULL && currentExam != NULL && currentExam->startTime >= endTime) || (prev != NULL && currentExam == NULL && prev->endTime <= endTime)
            || (prev != NULL && currentExam != NULL && prev->endTime <= endTime && currentExam->startTime >= endTime))
         {
            Exam* newExam = CreateExam(startTime, endTime, courseCode); //put newExam actually

            if(prev == NULL){   //exam is at head
                newExam->next = currentExam;
                targetDay->examList = newExam;
            }
            else{   // put btwn prev and currentExam
                prev->next = newExam;
                newExam->next = currentExam;
            }

            if(firstTry == 1){
                printf("%s exam added to %s at time %d to %d without conflict.\n", courseCode, day, startTime, endTime);
                return 0;
            }
            else if(firstTry == 0){
                printf("%s exam added to %s at time %d to %d due to conflict.\n", courseCode, targetDay->dayName, startTime, endTime);
                return 1;
            }
            examAdded = 1;

        }else if(globUpdFlag == 0){  //if conflict occured 
            firstTry = 0;
            int duration = endTime - startTime;
            if(currentExam !=NULL){startTime = currentExam->endTime; }
            else{printf("currentexam is null\n"); startTime = prev->endTime;}
            endTime = startTime +duration;
            
            
            
            if(startTime > 17){ //time slots for this day ended, look for next day
                printf("this day doesnt have more slots, looking for the next day\n");
                if(targetDay == NULL){
                    printf("targetday is NULL!!");
                    return -1;
                }
                targetDay = targetDay->nextDay;
                currentExam = targetDay->examList;
                prev = NULL;
                startTime = 8;
                endTime = startTime + duration;  //maintain duration
                count++; 
            }
            
        }
        globUpdFlag = 0;

    }   //endwhile(count<7)

        printf("Schedule full. Exam cannot be added.\n");
        return 2;

}

// Remove an exam from a specific day in the schedule
int RemoveExamFromSchedule(struct Schedule* schedule, const char* day, int startTime) {
    Day* targetDay = schedule->head;
    for(int i =0; i < 7; i++){
        if(strcmp(targetDay->dayName, day)==0){
            break;
        }
        targetDay = targetDay->nextDay;
    }

Exam* currentExam = targetDay->examList;
Exam* prevExam = NULL;

while(currentExam != NULL){
    if(currentExam->startTime == startTime){
        strcpy(globCourseCode, currentExam->courseCode);    //globalCourse code is set, used for Update function
        if(prevExam == NULL){
            targetDay->examList = currentExam->next;
        }
        else{
            prevExam->next = currentExam->next;
        }
        free(currentExam);
        printf("Exam removed successfully.\n");
        return 0;
    }
    prevExam = currentExam;
    currentExam = currentExam->next;
}
    printf("Exam could not be found.\n");
    return 1; // Exam not found
}

// Update an exam in the schedule
int UpdateExam(struct Schedule* schedule, const char* oldDay, int oldStartTime, const char* newDay, int newStartTime, int newEndTime) {
    globUpdFlag = 1; //upd is happening, dont do resch in add func

    if(newStartTime < 8 || newEndTime>20 || newEndTime-newStartTime>3){
        printf("Invalid exam.\n");
        return 3;   
    }

//find targetDay
    Day* targetDay = schedule->head;    //start from monday
    int found = 0;
    for(int i =0; i<7; i++){
        if(strcmp(targetDay->dayName, oldDay)==0){
            found =1;
            break;
        }
        targetDay = targetDay->nextDay;
    }
    if (!found) {
        printf("Error: Day %s not found in schedule.\n", oldDay);
        return -1; // Return or handle error if the day isn't found
    }

    Exam* currentExam = targetDay->examList;
    Exam* prevExam = NULL;
    char courseCode[50];
    int examFound = 0;

    while(currentExam != NULL){
        if(currentExam->startTime == oldStartTime){
            strcpy(courseCode, currentExam->courseCode);
            examFound =1;
            break;
        }
        prevExam = currentExam;
        currentExam = currentExam->next;
    }

    if(!examFound){ //if no value was assigned after traversing
        printf("Exam could not be found.\n");
        return 2;
    }

    int addResult = AddExamToSchedule(schedule, newDay, newStartTime, newEndTime, courseCode);
    if(addResult == 0){
        int removeResult = RemoveExamFromSchedule(schedule, oldDay, oldStartTime);  //should be defined here bc if addres==0
        if(removeResult == 0){
            printf("Update successful.\n");
            return 0;
        }
        else{
            printf("No such exam found.\n");        //exam is alreday added? should i delete it?
            return 2; 
        }
    } else {
        RemoveExamFromSchedule(schedule, newDay, newStartTime);
        printf("Update unsuccessful.\n");
        return 1;
    }

    return 0;
}


// Function to create a deep copy of the schedule
Schedule* DeepCopySchedule(Schedule* original) {
    if (original == NULL) {
        return NULL; 
    }

    Schedule* newSchedule = (Schedule*)malloc(sizeof(Schedule));
    if (newSchedule == NULL) {
        printf("Memory allocation failed for new schedule.\n");
        return NULL; 
    }
    newSchedule->head = NULL; // new schedules head

    Day* originalDay = original->head;
    Day* newFirstDay = NULL;
    Day* newLastDay = NULL;

    // Copy the days
    if (originalDay != NULL) {
        do {
            Day* newDay = (Day*)malloc(sizeof(Day));
            if (newDay == NULL) {
                printf("Memory allocation failed for new day.\n");
                return NULL; // malloc fail
            }

            // Copy dayname
            strcpy(newDay->dayName, originalDay->dayName);
            newDay->examList = NULL; 

            // Copy exams for current day
            Exam* originalExam = originalDay->examList;
            Exam* newLastExam = NULL;

            while (originalExam != NULL) {
                Exam* newExam = (Exam*)malloc(sizeof(Exam));
                if (newExam == NULL) {
                    printf("Memory allocation failed for new exam.\n");
                    return NULL; 
                }

                // Copy times, coursecode
                newExam->startTime = originalExam->startTime;
                newExam->endTime = originalExam->endTime;
                strcpy(newExam->courseCode, originalExam->courseCode);
                newExam->next = NULL;

                // Add the new exam to the new day's exam list
                if (newDay->examList == NULL) {
                    newDay->examList = newExam; // first 
                } else {
                    newLastExam->next = newExam; // link new exam
                }
                newLastExam = newExam; // last exam pointer
                originalExam = originalExam->next; 
            }

            // Add new day
            if (newFirstDay == NULL) {
                newFirstDay = newDay; 
            } else {
                newLastDay->nextDay = newDay; 
            }
            newLastDay = newDay; 

            originalDay = originalDay->nextDay; 
        } while (originalDay != NULL && originalDay != original->head);

        // circular
        if (newLastDay != NULL) {
            newLastDay->nextDay = newFirstDay; 
        }
    }

    newSchedule->head = newFirstDay; // first day 
    return newSchedule; // Return new
}


//Clear all exams from a specific day and relocate them to other days
int ClearDay(struct Schedule* schedule, const char* day) {

//find targetDay
    Day* targetDay = schedule->head;    //start from monday
    int found = 0;
    for(int i =0; i<7; i++){
        if(strcmp(targetDay->dayName, day)==0){
            found =1;
            break;
        }
        targetDay = targetDay->nextDay;
    }
    if (!found) {
        printf("Error: Day %s not found in schedule.\n", day);
        return -1; 
    }

    if(targetDay->examList == NULL){
        printf("%s is already clear.", targetDay->dayName);
        return 1;   //day is already clear
    }

    Exam* examToRelocate = targetDay->examList;
    
    Schedule* copiedSchedule = DeepCopySchedule(schedule);

    while(examToRelocate != NULL){
        int duration = examToRelocate->endTime - examToRelocate->startTime;
       

        int addResult = AddExamToSchedule(schedule, targetDay->nextDay->dayName, 8, 8+duration, examToRelocate->courseCode);
        if(addResult == 0 || addResult ==1){
            RemoveExamFromSchedule(schedule, targetDay->dayName, examToRelocate->startTime);
            //printf("Checkpoint: targetday is %s\n", targetDay->dayName);
            examToRelocate = examToRelocate->next;//traverse
        }else{
            schedule = copiedSchedule;  //return to original schedule without any additions
            DeleteSchedule(copiedSchedule); //free it
            copiedSchedule = NULL;
            printf("Schedule full. Exams from %s could not be relocated.\n", targetDay->dayName);
            return 2;
        }
    }

    printf("%s is cleared, exams relocated.\n", targetDay->dayName);
    return 0;
}

void DeleteExamsFromDay(Day* day) {
    if (day == NULL) return; 

    Exam* currentExam = day->examList;
    while (currentExam != NULL) {
        Exam* nextExam = currentExam->next; 
        free(currentExam); 
        currentExam = nextExam; 
    }
    day->examList = NULL; 
    
}

// Clear all exams and days from the schedule and deallocate memory
void DeleteSchedule(struct Schedule* schedule) {
    if (schedule == NULL) {
        return; // Nothing to delete
    }

    Day* currentDay = schedule->head;   //start from monady
    Day* nextDay;

    for(int i=0; i<7; i++){
        if(currentDay == NULL){
            break;
        }

        DeleteExamsFromDay(currentDay);
        nextDay = currentDay->nextDay;
        free(currentDay);
        currentDay = nextDay;
    }

    free(schedule);
    schedule->head = NULL;
    printf("Schedule is cleared.\n");
    return;
}


// Read schedule from file
int ReadScheduleFromFile(struct Schedule* schedule, const char* filename) {
    FILE* file = fopen(filename, "r");
    if (file == NULL) {
        perror("Couldn't open the file");
        return -1;
    }

    char dayName[MAX_DAY_NAME_LEN];
    int startTime, endTime;
    char courseCode[MAX_COURSE_CODE_LEN];


    while (fscanf(file, "%s", dayName) == 1) { // Read day name
        // Read exams for the current day
        while (fscanf(file, "%d %d %s", &startTime, &endTime, courseCode) == 3) {
            
            int addResult = AddExamToSchedule(schedule, dayName, startTime, endTime, courseCode);
            if (addResult != 0) {
                fprintf(stderr, "Error adding exam: %s %d %d %s\n", dayName, startTime, endTime, courseCode);
                fclose(file);
                return -1; 
            }
        }
    }

    fclose(file); 
    return 0; 
}


// Write schedule to file
int WriteScheduleToFile(struct Schedule* schedule, const char* filename) {
    FILE* file = fopen(filename, "w");
    if (file == NULL) {
        perror("Could not open the file for writing");
        return -1; 
    }

    Day* currentDay = schedule->head;
    if (currentDay == NULL) {
        fprintf(file, "No schedule available.\n"); 
        fclose(file);
        return 0; // No exams to write
    }

    do {
        fprintf(file, "%s\n", currentDay->dayName); 
        
        // Write exams for the current day
        struct Exam* currentExam = currentDay->examList;
        if (currentExam == NULL) {
            fprintf(file, "  No exams scheduled.\n"); 
        } else {
            while (currentExam != NULL) {
                fprintf(file, "  %d %d %s\n", currentExam->startTime, currentExam->endTime, currentExam->courseCode);
                currentExam = currentExam->next; 
            }
        }
        
        currentDay = currentDay->nextDay; 
    } while (currentDay != schedule->head); 

    fclose(file); 
    return 0; 
}


// Function to print all exams in the schedule
void PrintSchedule(const Schedule* schedule) {
    if (schedule == NULL || schedule->head == NULL) {
        printf("No schedule to display.\n");
        return;
    }

    const Day* currentDay = schedule->head;
    int isFirstDay = 1;

    do {
        printf("Day: %s\n", currentDay->dayName);

        Exam* currentExam = currentDay->examList;
        if (currentExam == NULL) {
            printf("  No exams scheduled.\n");
        } else {
            while (currentExam != NULL) {
                printf("  Exam: %s | Start: %d | End: %d\n", currentExam->courseCode, currentExam->startTime, currentExam->endTime);
                currentExam = currentExam->next;
            }
        }

        currentDay = currentDay->nextDay;
        isFirstDay = 0;

    } while (currentDay != schedule->head || isFirstDay);

    printf("Schedule printing complete.\n");
}
