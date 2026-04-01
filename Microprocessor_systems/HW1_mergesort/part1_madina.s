        AREA    MergeSort_M0, CODE, READONLY
        THUMB
        ENTRY
        EXPORT  main
        EXPORT  my_MergeSort
        EXPORT  my_Merge
        
main    PROC
;Fill in these functions according to the merge logic; you may use additional helper functions
   ; assign initial values to registers R0 to R4
    movs r0, #38    ; r0 <- 38
    movs r1, #27    ; r1 <- 27
    movs r2, #43    ; r2 <- 43
    movs r3, #10    ; r3 <- 10
    movs r4, #55    ; r4 <- 55

;Store these values into memory
    ldr r5, =Array_Data ;r5 now contains address of Array_Data in memory, 20 bytes for Array_Data are allocated
    stmia r5!, {r0-r4}  ; r0-r4 are stored in allocated space starting from r5, r5 is incremented

;Prep for mergesort		
    ldr r0, =Array_Data ;base address of array
    movs r1, #0 ; index of first element (left = 0)
    movs r2, #4 ; index of last element (right = 4)

    bl my_MergeSort ; go to mergesort, save return address

;load sorted values back into registers R0-R4
    ldr r5, =Array_Data ;r5 now contains address of Array_Data in memory
    ldmia r5!, {r0-r4}  ; load sorted values from memory into r0-r4

stop    B       stop ; put breakpoint here to work
        ENDP

my_MergeSort PROC
;Fill in these functions according to the merge logic; you may use additional helper functions
    push {r0-r7, lr}    ; save all registers and return addtess to stack(to restore upon return)

;base case of recursion, if left>right, then return
    cmp r1, r2  ; check if r1-r2 
    bge ms_end  ; if r1 is bigger, then go to ms_end

; find mid = (left + right) / 2
    adds r3, r1, r2 ; save sum of r1 and r2 in r3
    lsrs r3, r3, #1 ; divide sum by two  (floor division by 2 = lsrs)  

;my_MergeSort(arr, left, mid)
    push {r2}   ; save r2 (right index)
    movs r2, r3 ; now new right index is mid, assign r3 to r2
    bl my_MergeSort ; recursive call, goto my_MergeSort
    pop {r2}    ; restore right

;my_MergeSort(arr, mid+1, right)
    push {r1}   ; save r1 (left index)
    movs r1, r3 ; now new left index is mid, assign r3 to r1
    adds r1, r1, #1 ;increment r1 (left element starts from mid+1)
    bl my_MergeSort ; recursive call, goto my_MergeSort
    pop {r1}    ; restore left


; find mid = (left + right) / 2
    adds r3, r1, r2 ; save sum of r1 and r2 in r3
    lsrs r3, r3, #1 ; divide sum by two  (floor division by 2 = lsrs)  
    bl my_Merge ; myMerge(arr, left, mid, right)

ms_end
    pop {r0-r7, PC} ;restore all registers, return to caller function

    ENDP



; r0: array base
; r1: left
; r2: right
; r3: mid
my_Merge PROC
;Fill in these functions according to the merge logic; you may use additional helper functions
    push {r0-r7, lr}    ; save value in stack to restore at return

    sub SP, #8  ; make space for 2 registers on stack
    str r3, [SP, #0]    ; store mid on stack
    str r2, [SP, #4]    ; store right on stack

; r1 = i (left index)
; r2 = j (right index = mid+1)
    movs r2, r3 ; mid = right
    adds r2, r2, #1 ; mid++

    movs r3, #0 ; r3 =k (index for temp array, starts at 0)

    ldr r4, =Temp_Arr   ; address of temp array

merge_loop
    ; check i > mid
    ldr r5, [SP, #0]  ; load r5 with mid
    cmp r1, r5  ; is i>mid?
    bgt copy_j  ; if r1>r5 then goto copy_j

    ; check j > right
    ldr r5, [SP, #4]  ; load r5 with right
    cmp r2, r5  ; is j>right?
    bgt copy_i  ; if r1>r5 then goto copy_i

    ;compare array[i] vs array[j]
    lsls r5, r1, #2 ; get offset
    ldr r5, [r0, r5]    ; array[i]

    lsls    r6, r2, #2  ; get offset
	ldr     r6, [r0, r6]    ; array[j]

    cmp r5, r6  ; r5>r6?
    ble take_i  ; if r5 is smaller take i

take_j  ; if array[j]<array[i]
    lsls r7, r3, #2 ; r7 =k (get offset)
    str r6, [r4, r7]    ; temp[k] = array[j]
    adds r2, r2, #1 ; j++
    adds r3, r3, #1 ; k++
    b merge_loop    ;   loop

take_i ; if array[i]<array[j]
    lsls r7, r3, #2 ; r7 =k (get offset)
    str r5, [r4, r7]    ; temp[k] = array[i]
    adds r1, r1, #1 ; i++
    adds r3, r3, #1 ; k++
    b merge_loop    ;loop

copy_i
    ldr r5, [SP, #0]    ; r5 = mid
    cmp r1, r5  ; compare i and mid
    bgt copy_back   ; if i>mid, then goto copy_back

    lsls r5, r1, #2 ; get offset
    ldr r5, [r0, r5]    ;  load array[i] into R5

    lsls r6, r3, #2 ; get offset
    str r5, [r4, r6]    ; store array[i] in temp[k]
    adds r1, r1, #1 ; i++
    adds r3, r3, #1 ; k++
    B copy_i    ; goto copy_i

copy_j
    ldr r5, [SP, #4]    ; r5 = right
    cmp r2, r5  ; compare j and right
    bgt copy_back  ;goto copyback if r2>r5

    lsls r5, r2, #2    ; get offset
    ldr r5, [r0, r5] ;  load array[j] into R5

    lsls r6, r3, #2    ; get offset
    str r5, [r4, r6]    ; store array[j] in temp[k]
    adds r2, r2, #1 ; j++
    adds r3, r3, #1 ; k++
    B copy_j    ; goto copy_i

copy_back
    
    ldr r5, [sp, #4]    ; right
    subs r5, r5, r3     ; right -k
    adds r5, r5, #1     ; left = right - k +1

    movs r6, #0 ; indes for temp

cb_loop
    cmp r6, r3  ; r6>r3?
    bge m_update_regs   ; if r6>r3 then goto m_update_regs (shows steps)

    lsls r7, r6, #2 ; offset
    ldr r7, [r4, r7]    ; load from temp

    lsls r1, r5, #2 ;offset
    str r7, [r0, r1]    ; store into Arr

    adds r6, r6, #1 ; increment temp index
    adds r5, r5, #1 ; increment Arr index
    B cb_loop   ; loop until all elements copied

m_update_regs
    ldr r0, [SP, #8]    ; reload base address
    ldmia r0, {r0-r4}   ; load all value into r0-r4, this is overwritten when POP

m_end
    add SP, #8  ; restore stack pointer
    pop {r0-r7, PC} ; restore all registers, return to caller
    ENDP

	AREA    MyData, DATA, READWRITE
	ALIGN
Array_Data  SPACE   20      ; space for 5 words (5 * 4 bytes)
Temp_Arr    SPACE   20      ; space for 5 words
	
	END