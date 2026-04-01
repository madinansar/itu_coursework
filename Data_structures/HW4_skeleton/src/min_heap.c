#include <stddef.h>
#include "../include/min_heap.h"

static void swap(void* a, void* b, size_t element_size){
    void* temp = malloc(element_size);
    if(!temp){
        printf("malloc failed");
        exit(EXIT_FAILURE);
    }
    memcpy(temp, a, element_size);  //temp = a
    memcpy(a, b, element_size); //a = b
    memcpy(b, temp, element_size);  // b = temp
         free(temp);

}

static void bubble_up(MinHeap* heap, size_t index){
    while(index>0){
        size_t parent_index = (index - 1) / 2;
        void* current = (char*)heap->data + index*heap->element_size;
        void* parent = (char*)heap->data + parent_index*heap->element_size;

        if(heap->compare(current, parent)>=0){
            break;
        }
        swap(current, parent, heap->element_size);
        index = parent_index;
    }
}

static void bubble_down(MinHeap* heap, size_t index){
    size_t left_child, right_child, smallest;

    while(1){
        left_child = 2 * index + 1;
        right_child = 2 * index + 2;
        smallest = index;

        void* current = (char*)heap->data + index * heap->element_size;
        if(left_child < heap->size){
            void* left = (char*)heap->data + left_child*heap->element_size;
            if(heap->compare(left, current) < 0){
                smallest = left_child;
            }
        }

        if(right_child<heap->size){
            void* right = (char*)heap->data + right_child*heap->element_size;
            void* smallest_element = (char*)heap->data + smallest * heap->element_size;
            if(heap->compare(right, smallest_element)<0){
                smallest = right_child;
            }
        }
        if(smallest == index){
            break;
        }
        swap(current, (char*)heap->data + smallest * heap->element_size, heap->element_size);
        index = smallest;

    }
}


MinHeap* heap_create(size_t capacity, size_t element_size, int (*compare)(const void*, const void*)){
    MinHeap* heap = malloc(sizeof(MinHeap));    //do i need (MinHeap*) casting?
    if(!heap) return NULL;  //malloc fails
    heap->data = malloc(element_size*capacity);
    if(!heap->data) return NULL;    //malloc fails

    heap->element_size = element_size;
    heap->capacity = capacity;
    heap->compare = compare;
    heap->size = 0;

    return heap;
}

void heap_destroy(MinHeap* heap){
    if(heap){
        free(heap->data);
        free(heap);
    }
}

int heap_insert(MinHeap* heap, const void* element){
    if(heap->size == heap->capacity){
        size_t new_capacity = 2*heap->capacity; //double current cap
        void* new_data = realloc(heap->data, new_capacity*heap->element_size);
        if(!new_data) return 0;  //realloc fails

        heap->data = new_data;
        heap->capacity = new_capacity;
    }
    void* target = (char*)heap->data + heap->size * heap->element_size;
    memcpy(target, element, heap->element_size);
    bubble_up(heap, heap->size);
    heap->size++;
    return 1;
}

int heap_extract_min(MinHeap* heap, void* result){
    if(heap->size == 0){
        return 0;   //fails
    }
    void* root = heap->data;
    memcpy(result, root, heap->element_size);
    heap->size--;
    if(heap->size > 0){
        void* last_element = (char*)heap->data + heap->size*heap->element_size;
        memcpy(root, last_element, heap->element_size);
        bubble_down(heap, 0);
    }
    return 1;   //success
}

int heap_peek(const MinHeap* heap, void* result){
    if(heap->size == 0){ return 0; }

    memcpy(result, heap->data, heap->element_size);
    return 1;
}

size_t heap_size(const MinHeap* heap){
    return heap->size;
}

int heap_merge(MinHeap* heap1, const MinHeap* heap2){
    if(heap1->element_size != heap2->element_size || heap1->compare != heap2->compare){
        return 0;
    }

    for(size_t i=0; i<heap2->size; i++){
        void* element = (char*) heap2->data + i*heap2->element_size;
        if(!heap_insert(heap1, element)){
            return 0;
        }
    }
    return 1;
}