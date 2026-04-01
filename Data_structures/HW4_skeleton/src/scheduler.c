#include <stdlib.h>
#include "../include/scheduler.h"

int compare_processes(const void* a, const void* b) {
    const Process* p1 = (const Process*)a;
    const Process* p2 = (const Process*)b;
    return p1->vruntime - p2->vruntime;
}

Scheduler* create_scheduler(int capacity){
    Scheduler* scheduler = malloc(sizeof(Scheduler));

    if(!scheduler){
        printf("scheduler malloc failed");
        return NULL;
    }

    scheduler->process_queue = heap_create(capacity, sizeof(Process), compare_processes);
    
    if (!scheduler->process_queue) {
        free(scheduler);
        printf("process queue failed");
        return NULL;
    }
    scheduler->current_process = NULL;
    scheduler->time_slice = 100;    //check!!
    return scheduler;
}


void destroy_scheduler(Scheduler* scheduler) {
    if (!scheduler) return;

    if (scheduler->current_process) {
        free(scheduler->current_process); 
    }
    heap_destroy(scheduler->process_queue); 
    free(scheduler); 
}


void schedule_process(Scheduler* scheduler, Process process) {
    if (!scheduler || !scheduler->process_queue) return;

    if (!heap_insert(scheduler->process_queue, &process)) {
        fprintf(stderr, "failed pid: %d", process.pid);
    }
}

/*
 * Retrieves the next process to be executed based on virtual runtime.
 */
Process* get_next_process(Scheduler* scheduler) {
    if (!scheduler || !scheduler->process_queue) return NULL;

    if (scheduler->current_process) {
        scheduler->current_process->is_running = false;
        heap_insert(scheduler->process_queue, scheduler->current_process);
        free(scheduler->current_process);
        scheduler->current_process = NULL;
    }

    Process temp;
    if (heap_extract_min(scheduler->process_queue, &temp)) {
        scheduler->current_process = malloc(sizeof(Process));
        if (!(scheduler->current_process)) {
            perror("malloc fail next process");
            return NULL;
        }
        *scheduler->current_process = temp;
        scheduler->current_process->is_running = true;
    }

    return scheduler->current_process;
}


/*
 * Updates the scheduler state for one time slice unit.
 */
void tick(Scheduler* scheduler) {
    if (!scheduler || !scheduler->current_process) return;

    update_vruntime(scheduler->current_process, scheduler->time_slice);
    heap_insert(scheduler->process_queue, scheduler->current_process);
    scheduler->current_process = NULL;
}


