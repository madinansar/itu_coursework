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

void log_event(const char *event) {
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    fprintf(log_file, "[%02d:%02d:%02d] [INFO] %s\n", t->tm_hour, t->tm_min, t->tm_sec, event);
    fflush(log_file);
}

void read_jobs(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open jobs.txt");
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

int find_next_job(int current_pid) {
    int min_priority = 1000, min_index = -1;
    
    for (int i = 0; i < num_jobs; i++) {
        if (jobs[i].remaining_time > 0) {
            if (jobs[i].priority < min_priority) {
                min_priority = jobs[i].priority;
                min_index = i;
            } else if (jobs[i].priority == min_priority) {
                if (jobs[i].arrival_time < jobs[min_index].arrival_time) {
                    min_index = i;
                } else if (jobs[i].arrival_time == jobs[min_index].arrival_time &&
                           jobs[i].remaining_time < jobs[min_index].remaining_time) {
                    min_index = i;
                }
            }
        }
    }
    
    return min_index;
}

void scheduler() {
    int current_job = -1;
    int time_elapsed = 0;

    while (1) {
        int next_job = find_next_job(current_job);
        if (next_job == -1) break;  // No remaining jobs

        if (jobs[next_job].pid == 0) {  
            pid_t pid = fork();
            if (pid == 0) {
                char exec_cmd[30];
                sprintf(exec_cmd, "./%s", jobs[next_job].name);
                execlp(exec_cmd, jobs[next_job].name, NULL);
                exit(0);
            } else {
                jobs[next_job].pid = pid;
                char log_msg[100];
                sprintf(log_msg, "Forking new process for %s (PID: %d)", jobs[next_job].name, pid);
                log_event(log_msg);
            }
        } else {
            kill(jobs[next_job].pid, SIGCONT);
            char log_msg[100];
            sprintf(log_msg, "Resuming job %s (PID: %d)", jobs[next_job].name, jobs[next_job].pid);
            log_event(log_msg);
        }

        sleep(time_slice);
        time_elapsed += time_slice;
        jobs[next_job].remaining_time -= time_slice;

        if (jobs[next_job].remaining_time > 0) {
            kill(jobs[next_job].pid, SIGSTOP);
            char log_msg[100];
            sprintf(log_msg, "Job %s ran for %d seconds. Sending SIGSTOP (PID: %d)", 
                    jobs[next_job].name, time_slice, jobs[next_job].pid);
            log_event(log_msg);
        } else {
            waitpid(jobs[next_job].pid, NULL, 0);
            char log_msg[100];
            sprintf(log_msg, "Job %s completed execution. Terminating (PID: %d)", 
                    jobs[next_job].name, jobs[next_job].pid);
            log_event(log_msg);
        }
    }
}

int main() {
    log_file = fopen(LOG_FILE, "w");
    if (!log_file) {
        perror("Failed to open log file");
        return EXIT_FAILURE;
    }

    read_jobs("jobs.txt");
    scheduler();

    fclose(log_file);
    return 0;
}
