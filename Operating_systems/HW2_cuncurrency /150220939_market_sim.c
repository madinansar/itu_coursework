#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <stdarg.h>
#include <time.h>
#include "market_sim.h"

int num_customers, num_products, reservation_timeout_ms, max_concurrent_payments;
Stock stock[MAX_PRODUCTS];
RequestThread requests[MAX_REQUESTS];
int active_customers[MAX_CUSTOMERS];  
int request_count = 0;
int current_payments = 0;
int active_count = 0;  

pthread_mutex_t stock_mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t log_mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t payment_mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t payment_cond = PTHREAD_COND_INITIALIZER;
pthread_cond_t product_cond[MAX_PRODUCTS]; 
void initialize_product_conditions() {
    for (int i = 0; i < num_products; i++) {
        pthread_cond_init(&product_cond[i], NULL);
    }
}



FILE* log_file;

long current_time_ms() {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return ts.tv_sec * 1000L + ts.tv_nsec / 1000000L;
}


void log_action(const char* format, ...) {
    pthread_mutex_lock(&log_mutex);

    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    time_t now_sec = ts.tv_sec;
    struct tm now_tm;
    localtime_r(&now_sec, &now_tm);

    char time_buffer[64];
    int millis = ts.tv_nsec / 1000000;
    strftime(time_buffer, sizeof(time_buffer), "%Y-%m-%d %H:%M:%S", &now_tm);

    fprintf(log_file, "[%s.%03d] [Thread %lu] ", time_buffer, millis, (unsigned long)pthread_self());

    va_list args;
    va_start(args, format);
    vfprintf(log_file, format, args);
    va_end(args);

    fprintf(log_file, "\n");
    fflush(log_file);
    pthread_mutex_unlock(&log_mutex);
}


void parse_input(const char* filename) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        perror("input.txt");
        exit(EXIT_FAILURE);
    }


    char line[MAX_LINE];
    int config_lines_read = 0;
    int group_id=0;

    while (fgets(line, sizeof(line), file)) {
        char* trimmed = line;

        if (line[0] == '\n' || (line[0] == '\r' && line[1] == '\n') || line[0] == '\0') {
            group_id++; 
            continue;  
        }

        // First 5 lines are config
        if (config_lines_read < 5) {
            if (strncmp(trimmed, "num_customers=", 14) == 0){
                num_customers = atoi(trimmed + 14);
                printf("Number of customers: %d\n", num_customers);
            }
                
            else if (strncmp(trimmed, "num_products=", 13) == 0){
                num_products = atoi(trimmed + 13);
                printf("Number of products: %d\n", num_products);
            }
            else if (strncmp(trimmed, "reservation_timeout_ms=", 23) == 0){
                reservation_timeout_ms = atoi(trimmed + 23);
                printf("Timeout (ms): %d\n", reservation_timeout_ms);
            }
                
            else if (strncmp(trimmed, "max_concurrent_payments=", 24) == 0){
                max_concurrent_payments = atoi(trimmed + 24);
                printf("Max concurrent payments: %d\n", max_concurrent_payments);
            }

            else if (strncmp(trimmed, "initial_stock=", 14) == 0) {
                char* token = strtok(trimmed + 14, ",");
                int i = 0;
                while (token && i < num_products) {
                    stock[i].quantity = atoi(token);
                    stock[i].reserved = 0;
                    i++;
                    token = strtok(NULL, ",");
                }
            }
            config_lines_read++;
        } else {

            ProductRequest pr;
            if (sscanf(trimmed, "%d,%d,%d", &pr.customer_id, &pr.product_id, &pr.quantity) == 3) {
                requests[request_count].request = pr;
                requests[request_count].purchased = 0;
                requests[request_count].reservation_time = 0;
                requests[request_count].group_id = group_id;
                printf("Request %d: Customer %d requested %d unit(s) of Product %d (group_id: %d)\n",
                    request_count + 1,
                    pr.customer_id,
                    pr.quantity,
                    pr.product_id,
                    group_id);
                request_count++;
            }
        }
    }
    fclose(file);
}

pthread_mutex_t active_mutex = PTHREAD_MUTEX_INITIALIZER;  

int is_customer_active(int customer_id) {
    for (int i = 0; i < active_count; i++) {
        if (active_customers[i] == customer_id) {
            return 1;  
        }
    }
    return 0; 
}

void add_customer_to_active(int customer_id) {
    pthread_mutex_lock(&active_mutex);
    if (active_count < MAX_CUSTOMERS) {
        active_customers[active_count++] = customer_id; 
    }
    pthread_mutex_unlock(&active_mutex);
}

void remove_customer_from_active(int customer_id) {
    pthread_mutex_lock(&active_mutex);
    for (int i = 0; i < active_count; i++) {
        if (active_customers[i] == customer_id) {
            // Shift
            for (int j = i; j < active_count - 1; j++) {
                active_customers[j] = active_customers[j + 1];
            }
            active_count--;  
            break;
        }
    }
    pthread_mutex_unlock(&active_mutex);
}
int get_active_customer_count() {
    pthread_mutex_lock(&active_mutex);
    int count = active_count;
    pthread_mutex_unlock(&active_mutex);
    return count;
}

void log_active_customers() {
    pthread_mutex_lock(&active_mutex);

    char buffer[256];
    int offset = snprintf(buffer, sizeof(buffer), "Active customers [%d]: ", active_count);

    for (int i = 0; i < active_count && offset < sizeof(buffer); i++) {
        offset += snprintf(buffer + offset, sizeof(buffer) - offset, "%d ", active_customers[i]);
    }

    log_action(buffer);

    pthread_mutex_unlock(&active_mutex);
}

void* handle_request(void* arg) {
    RequestThread* req = (RequestThread*)arg;
    int cid = req->request.customer_id;
    int pid = req->request.product_id;
    int qty = req->request.quantity;

    pthread_mutex_lock(&stock_mutex);
    log_action("Customer %d attempting to add product %d (qty: %d) to cart | Stock: [", cid, pid, qty);
    for (int i = 0; i < num_products; i++) {
        fprintf(log_file, " product %d: %d,", i, stock[i].quantity);
    }
    fprintf(log_file, " ]\n");


    if (stock[pid].quantity >= qty) {
        stock[pid].quantity -= qty;
        stock[pid].reserved += qty;
        req->reservation_time = current_time_ms();

        log_action("Customer %d successfully reserved product %d (qty: %d) | Updated Stock: [", cid, pid, qty);
        for (int i = 0; i < num_products; i++) {
            fprintf(log_file, " product %d: %d,", i, stock[i].quantity);
        }
        fprintf(log_file, " ]\n");

        printf("Customer %d reserved product %d (qty: %d)\n", cid, pid, qty);
    } else {
        log_action("Customer %d failed to reserve product %d (qty: %d) — only %d available",
                   cid, pid, qty, stock[pid].quantity);
        printf("Customer %d failed to reserve product %d (qty: %d) — only %d available\n",
                   cid, pid, qty, stock[pid].quantity);

        pthread_cond_wait(&product_cond[pid], &stock_mutex);
        pthread_mutex_unlock(&stock_mutex);
        return NULL;
    }

    pthread_mutex_unlock(&stock_mutex);


    int will_purchase = rand() % 2;
    //int will_purchase = 1;
    if (!will_purchase) {
        usleep(reservation_timeout_ms * 1000);
        pthread_mutex_lock(&stock_mutex);
        stock[pid].quantity += qty;
        stock[pid].reserved -= qty;
        log_action("Customer will not buy. Customer %d timeout expired. Product %d (qty: %d) returned to stock | Updated Stock: [", cid, pid, qty);
        for (int i = 0; i < num_products; i++) {
            fprintf(log_file, " product %d: %d,", i, stock[i].quantity);
        }
        fprintf(log_file, " ]\n");

        printf("Customer will not buy. Customer %d timeout expired. Product %d (qty: %d) returned to stock\n",
                   cid, pid, qty);
        remove_customer_from_active(req->request.customer_id);
        pthread_cond_signal(&product_cond[pid]); 
        pthread_mutex_unlock(&stock_mutex);
        return NULL;
    }

    long start = req->reservation_time;
    int acquired_payment = 0;
    
    while ((current_time_ms() - start) < reservation_timeout_ms) {
        log_action("Customer %d attempting to acquire payment slot...", cid);
        log_active_customers();
        pthread_mutex_lock(&payment_mutex);
        if (get_active_customer_count() < max_concurrent_payments || is_customer_active(req->request.customer_id)) {
            if(!is_customer_active(req->request.customer_id)){
                add_customer_to_active(req->request.customer_id);
            }
            acquired_payment = 1;
            pthread_mutex_unlock(&payment_mutex);
            break;
        }
        pthread_cond_wait(&payment_cond, &payment_mutex);
        pthread_mutex_unlock(&payment_mutex);
    }

    if (acquired_payment) {
        usleep(3000000); //3s
        pthread_mutex_lock(&stock_mutex);
        stock[pid].reserved -= qty;
        log_action("Customer %d purchased product %d (qty: %d) | Updated Stock: [ ", cid, pid, qty);
                for (int i = 0; i < num_products; i++) {
            fprintf(log_file, " product %d: %d,", i, stock[i].quantity);
        }
        fprintf(log_file, " ]\n");

        printf("Customer %d purchased product %d (qty: %d)\n", cid, pid, qty);
        pthread_mutex_unlock(&stock_mutex);

        pthread_mutex_lock(&payment_mutex);
        remove_customer_from_active(req->request.customer_id);
        pthread_cond_signal(&payment_cond);
        pthread_mutex_unlock(&payment_mutex);
    } else {
        pthread_mutex_lock(&stock_mutex);
        stock[pid].quantity += qty;
        stock[pid].reserved -= qty;
        log_action("Customer will not buy. Customer %d timeout expired. Product %d (qty: %d) returned to stock | Updated Stock: [", cid, pid, qty);
        for (int i = 0; i < num_products; i++) {
            fprintf(log_file, " product %d: %d,", i, stock[i].quantity);
        }
        fprintf(log_file, " ]\n");

        printf("Customer %d failed to purchase product %d (qty: %d). Timeout expired.\n",
                   cid, pid, qty);
        remove_customer_from_active(req->request.customer_id);
        pthread_cond_signal(&product_cond[pid]);    //wake up waiting of that product
        pthread_mutex_unlock(&stock_mutex);
    }

    return NULL;
}

int main() {
    srand(time(NULL));
    parse_input("input.txt");
    log_file = fopen("log.txt", "w");
    setvbuf(log_file, NULL, _IONBF, 0);

    log_action("Initial Stock:");
    int current_group = 0;
    int i = 0;

    while (i < request_count) {
        // current group
        while (i < request_count && requests[i].group_id == current_group) {
            pthread_create(&requests[i].thread, NULL, handle_request, &requests[i]);
            i++;
        }
        current_group++;
        usleep(1000000);  // 1s
        
    }

    for (int j = 0; j < request_count; j++) {
        pthread_join(requests[j].thread, NULL);
    }

    fclose(log_file);
    return 0;
}



