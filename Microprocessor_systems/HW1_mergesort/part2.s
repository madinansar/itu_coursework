        AREA    MergeSort_M0, CODE, READONLY
        THUMB
        ENTRY
        EXPORT  main
        EXPORT  my_MergeSort
        EXPORT  my_Merge

main    PROC
	; load base address of array into r7
	ldr     r7, =Array_Data ; r7 now contains address of Array_Data in memory

	;Prep for mergesort
	; r0 = left index (0), r1 = right index 
	movs    r0, #0          ; index of first element (left = 0)
	movs    r1, #7          ; index of last element (right = 7, since we have 8 elements)

	bl      my_MergeSort    ; go to mergesort, save return address

	;load sorted values back into registers r0-r7
	ldr     r7, =Array_Data ; reload r7 with base address (to be safe)
	ldmia   r7, {r0-r7}     ; load all 8 sorted values from memory into r0-r7

stop    b       stop            ; put breakpoint here to work
	ENDP

; r7: array base address
; r0: left index
; r1: right index
my_MergeSort PROC
	push    {r0-r7, lr}     ; save all registers and return address to stack (to restore upon return)

	;base case of recursion, if left >= right, then return
	cmp     r0, r1          ; compare left and right indices
	bge     ms_end          ; if left >= right, subarray has 0 or 1 element, go to ms_end

	; find mid = (left + right) / 2
	adds    r2, r0, r1      ; save sum of left and right in r2
	lsrs    r2, r2, #1      ; divide sum by two (floor division by 2 = lsrs)

	;my_MergeSort(arr, left, mid) 
	push    {r1}            ; save r1 (right index) on stack
	movs    r1, r2          ; now new right index is mid, assign r2 to r1
	bl      my_MergeSort    ; recursive call, goto my_MergeSort for left half
	pop     {r1}            ; restore original right index

	;my_MergeSort(arr, mid+1, right) 
	push    {r0}            ; save r0 (left index) on stack
	movs    r0, r2          ; now new left index is mid, assign r2 to r0
	adds    r0, r0, #1      ; increment r0 (left element starts from mid+1)
	bl      my_MergeSort    ; recursive call, goto my_MergeSort for right half
	pop     {r0}            ; restore original left index

	; find mid = (left + right) / 2 
	adds    r2, r0, r1      ; save sum of left and right in r2
	lsrs    r2, r2, #1      ; divide sum by two (floor division by 2 = lsrs)
	bl      my_Merge        ; my_Merge(arr, left, mid, right) - merge the two sorted halves

ms_end
	pop     {r0-r7, pc}     ; restore all registers, return to caller function
	ENDP

; r7: array base address
; r0: left index
; r1: right index
; r2: mid index
; r4: holds each merged element value
my_Merge PROC
	push    {r0-r7, lr}     ; save all registers to stack to restore at return

	sub     sp, #12         ; make space for 3 values on stack (mid, right, temp_base)
	str     r2, [sp, #0]    ; store mid on stack at offset 0
	str     r1, [sp, #4]    ; store right on stack at offset 4
	
	; save temp array base address on stack
	ldr     r3, =Temp_Arr
	str     r3, [sp, #8]    ; store temp base at offset 8

	; r0 = i (starts at left index)
	; r1 = j (starts at mid + 1)
	movs    r1, r2          ; j = mid
	adds    r1, r1, #1      ; j = mid + 1 (start of right half)

	; r2 = k (index for temp array, starts at 0)
	movs    r2, #0          ; k = 0, index for writing to temp array

merge_loop
	; check if i > mid 
	ldr     r3, [sp, #0]    ; load mid from stack into r3
	cmp     r0, r3          ; compare i with mid
	bgt     copy_j          ; if i > mid, left half done, copy remaining from right

	; check if j > right 
	ldr     r3, [sp, #4]    ; load right from stack into r3
	cmp     r1, r3          ; compare j with right
	bgt     copy_i          ; if j > right, right half done, copy remaining from left

	; compare array[i] vs array[j]
	; array base is in r7
	lsls    r3, r0, #2      ; get offset
	ldr     r3, [r7, r3]    ; load array[i] into r3

	lsls    r5, r1, #2      ; get offset for index j 
	ldr     r5, [r7, r5]    ; load array[j] into r5

	cmp     r3, r5          ; compare array[i] vs array[j]
	ble     take_i          ; if array[i] <= array[j], take from left half

take_j  ; array[j] < array[i], take element from right half
	movs    r4, r5          ; R4 = merged element value
r4_show_j                   
	ldr     r6, [sp, #8]    ; load temp base from stack
	lsls    r3, r2, #2      ; get offset for index k
	str     r4, [r6, r3]    ; temp[k] = r4 (merged element)
	adds    r1, r1, #1      ; j++
	adds    r2, r2, #1      ; k++
	b       merge_loop      ; continue merge

take_i  ; array[i] <= array[j], take element from left half
	movs    r4, r3          ; R4 = merged element value
r4_show_i                   
	ldr     r6, [sp, #8]    ; load temp base from stack
	lsls    r3, r2, #2      ; get offset for index k 
	str     r4, [r6, r3]    ; temp[k] = r4 (merged element)
	adds    r0, r0, #1      ; i++
	adds    r2, r2, #1      ; k++
	b       merge_loop      ; continue merge

copy_i  ; copy remaining elements from left half
	ldr     r3, [sp, #0]    ; load mid from stack into r3
	cmp     r0, r3          ; compare i with mid
	bgt     copy_back       ; if i > mid, all left elements copied, go to copy_back

	lsls    r3, r0, #2      ; get offset for index i
	ldr     r3, [r7, r3]    ; load array[i] into r3
	movs    r4, r3          ; R4 = merged element value 
r4_show_ci                  
	ldr     r6, [sp, #8]    ; load temp base from stack
	lsls    r5, r2, #2      ; get offset for index k
	str     r4, [r6, r5]    ; temp[k] = r4 (merged element)
	adds    r0, r0, #1      ; i++
	adds    r2, r2, #1      ; k++
	b       copy_i          ; continue copying remaining left elements

copy_j  ; copy remaining elements from right half
	ldr     r3, [sp, #4]    ; load right from stack into r3
	cmp     r1, r3          ; compare j with right
	bgt     copy_back       ; if j > right, all right elements copied, go to copy_back

	lsls    r3, r1, #2      ; get offset for index j 
	ldr     r3, [r7, r3]    ; load array[j] into r3
	movs    r4, r3          ; R4 = merged element value 
r4_show_cj                 
	ldr     r6, [sp, #8]    ; load temp base from stack
	lsls    r5, r2, #2      ; get offset for index k 
	str     r4, [r6, r5]    ; temp[k] = r4 (merged element)
	adds    r1, r1, #1      ; j++
	adds    r2, r2, #1      ; k++
	b       copy_j          ; continue copying remaining right elements

copy_back  ; copy all elements from temp array back to original array
	ldr     r3, [sp, #4]    ; load right from stack
	subs    r3, r3, r2      ; right - k (k = number of elements merged)
	adds    r3, r3, #1      ; left = right - k + 1 (original starting index)

	movs    r5, #0          ; r5 = index for temp (0)
	ldr     r6, [sp, #8]    ; load temp base from stack

cb_loop  ; loop to copy from temp back to original array
	cmp     r5, r2          ; compare temp index with k (total elements to copy)
	bge     m_end           ; if all elements copied, goto m_end

	lsls    r4, r5, #2      ; get byte offset for temp index (r5 * 4)
	ldr     r4, [r6, r4]    ; load element from temp[r5] into R4

	lsls    r0, r3, #2      ; get byte offset for array index (r3 * 4)
	str     r4, [r7, r0]    ; store element into array[r3] (r7 is array base)

	adds    r5, r5, #1      ; increment temp index
	adds    r3, r3, #1      ; increment array index
	b       cb_loop         ; loop until all elements copied back

m_end
	add     sp, #12         ; restore stack pointer
	pop     {r0-r7, pc}     ; restore all registers, return to caller
	ENDP

	AREA    MyData, DATA, READWRITE
	ALIGN
Array_Data  DCD     13, 27, 10, 7, 22, 56, 28, 2  ; 8 unsorted elements
Array_Size  DCD     8                             ; size of array
Temp_Arr    SPACE   32                            ; space for 8 elements (8 * 4 bytes)

	END
