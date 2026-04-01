//Madina Alzhanova 150220939

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <time.h>

#define MAX_JOBS 100
#define LOG_FILE "scheduler.log"

typedef struct {
    char name[20];
    int arrival_time;
    int priority;
    int execution_time;
    pid_t pid;
    int remaining_time;
} Job;

Job jobs[MAX_JOBS];
int num_jobs = 0;
int time_slice;
FILE *log_file;


void log_event(const char *event, const char *type) {
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    
    fprintf(log_file, "[%04d-%02d-%02d %02d:%02d:%02d] [%s] %s\n",
            t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
            t->tm_hour+3, t->tm_min, t->tm_sec, type, event);
    
    fflush(log_file);
}

void read_jobs(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open jobs.txt");
        log_event("Failed to open jobs.txt", "ERROR");
        exit(EXIT_FAILURE);
    }
    
    fscanf(file, "TimeSlice %d", &time_slice);
    
    while (fscanf(file, "%s %d %d %d", jobs[num_jobs].name, 
                  &jobs[num_jobs].arrival_time, 
                  &jobs[num_jobs].priority, 
                  &jobs[num_jobs].execution_time) != EOF) {
        jobs[num_jobs].remaining_time = jobs[num_jobs].execution_time;
        num_jobs++;
    }
    
    fclose(file);
}

int find_next_job(int last_executed_index, int current_time) {
    int min_priority = 1000, min_index = -1;
    int all_completed = 1;  

    for (int i = 0; i < num_jobs; i++) {
        if (jobs[i].remaining_time > 0 && jobs[i].arrival_time <= current_time) {   //if job is arrived
            all_completed = 0; 

            if (i != last_executed_index) {  
                if (jobs[i].priority < min_priority) {  //compare by priority
                    min_priority = jobs[i].priority;
                    min_index = i;

                } else if (jobs[i].priority == min_priority) {
                    if (jobs[i].arrival_time < jobs[min_index].arrival_time) {  //compare by arrival time
                        min_index = i;

                    } else if (jobs[i].arrival_time == jobs[min_index].arrival_time &&
                               jobs[i].remaining_time < jobs[min_index].remaining_time) {   //compare by remainig time
                        min_index = i;
                    }
                }
            }
        }
    }

    if (all_completed) {
        return -1;
    }
//same job 
    if (min_index == -1) {
        return last_executed_index;
    }

    return min_index;
}

void scheduler() {
    int current_job = -1;
    int current_time = 0;

    while (1) {
        int next_job = find_next_job(current_job, current_time);
        if (next_job == -1) {  
            log_event("All jobs completed. Exiting scheduler.", "INFO");
            break; 
        }

        if (jobs[next_job].pid == 0) { 

            //forking
            pid_t pid = fork();
            if (pid < 0) {
                log_event("Fork failed. Process creation error.", "ERROR");
                perror("Fork failed");
                exit(EXIT_FAILURE);
            }
            else if (pid == 0) {
                char exec_cmd[30];
                sprintf(exec_cmd, "./%s", jobs[next_job].name);
                execlp(exec_cmd, jobs[next_job].name, NULL);
                exit(0);
            } else {
                jobs[next_job].pid = pid;
                char log_msg[100];
                sprintf(log_msg, "Forking new process for %s (PID: %d)", jobs[next_job].name, pid);
                log_event(log_msg, "INFO");
            }
        } else {
            if (jobs[next_job].remaining_time > 0) {
                kill(jobs[next_job].pid, SIGCONT); //SIGCONT
                char log_msg[100];
                sprintf(log_msg, "Resuming job %s (PID: %d) - SIGCONT", jobs[next_job].name, jobs[next_job].pid);
                log_event(log_msg, "INFO");
            }
        }

        sleep(time_slice);
        jobs[next_job].remaining_time -= time_slice;
        current_time += time_slice; 
        current_job = next_job;  

        if (jobs[next_job].remaining_time > 0) {
            kill(jobs[next_job].pid, SIGSTOP);  //SIGSTOP
            char log_msg[100];
            sprintf(log_msg, "Job %s ran for %d seconds. Sending SIGSTOP (PID: %d)", 
                    jobs[next_job].name, time_slice, jobs[next_job].pid);
            log_event(log_msg,"INFO");
        } else {
            waitpid(jobs[next_job].pid, NULL, 0);
            char log_msg[100];
            sprintf(log_msg, "Job %s completed execution. Terminating (PID: %d)", 
                    jobs[next_job].name, jobs[next_job].pid);
            log_event(log_msg, "INFO");
            jobs[next_job].pid = -1;  //completed
        }
    }
}

int main() {
    log_file = fopen(LOG_FILE, "w");
    if (!log_file) {
        perror("Failed to open log file");
        log_event("Failed to open log file", "ERROR");
        return EXIT_FAILURE;
    }

    read_jobs("jobs.txt");
    scheduler();

    fclose(log_file);
    return 0;
}
