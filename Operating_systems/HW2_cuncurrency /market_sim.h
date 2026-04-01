#ifndef MARKET_SIM_H
#define MARKET_SIM_H

#include <pthread.h>
#include <time.h>

#define MAX_PRODUCTS 3
#define MAX_CUSTOMERS 5
#define MAX_REQUESTS 500
#define MAX_LINE 256

typedef struct {
    int customer_id;
    int product_id;
    int quantity;
    
} ProductRequest;

typedef struct {
    int quantity;
    int reserved;
} Stock;

typedef struct {
    ProductRequest request;
    long reservation_time;
    int purchased;
    pthread_t thread;
    int group_id;
} RequestThread;

void* handle_request(void* arg);
long current_time_ms();
void log_action(const char* format, ...);

#endif
