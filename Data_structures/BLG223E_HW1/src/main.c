#include "schedule.h"
#include "exam.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>


int main() {

    // const char* inputFile = "/workspaces/BLG223E-2024/.devcontainer/.vscode/BLG223E_HW1/exam_schedule_input.txt";
    // const char* outputFile = "/workspaces/BLG223E-2024/.devcontainer/.vscode/BLG223E_HW1/exam_schedule_output.txt";
   // ReadScheduleFromFile(schedule, inputFile);


    Schedule* schedule = CreateSchedule();

    // Add two back-to-back exams on Monday
    AddExamToSchedule(schedule, "Monday", 9, 11, "BLG113E");
    AddExamToSchedule(schedule, "Monday", 11, 12, "BLG212E");
    AddExamToSchedule(schedule, "Monday", 12, 14, "BLG102E");

    // Add one exam in the middle of Tuesday
    AddExamToSchedule(schedule, "Tuesday", 11, 14, "BLG223E");

    // Clear Monday (exams should be relocated to Tuesday)
    ClearDay(schedule, "Monday");

    PrintSchedule(schedule);
    // Write schedule to file
    //WriteScheduleToFile(schedule, outputFile);

    DeleteSchedule(schedule);


    return 0;
}
