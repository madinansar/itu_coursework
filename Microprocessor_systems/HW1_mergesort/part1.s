	AREA    MergeSort_M0, CODE, READONLY
	THUMB
	ENTRY
	EXPORT  main
	EXPORT  my_MergeSort
	EXPORT  my_Merge

main
	; 1. Initialize registers with unsorted values (Part 1 Requirement)
	MOVS    R0, #38
	MOVS    R1, #27
	MOVS    R2, #43
	MOVS    R3, #10
	MOVS    R4, #55
	
	; 2. Store these values to memory so we can sort them
	LDR     R5, =Array_Data
	STMIA   R5!, {R0-R4}    ; Store R0-R4 to [R5]
	
	; 3. Prepare for MergeSort
	LDR     R0, =Array_Data ; Base Address
	MOVS    R1, #0          ; Left Index
	MOVS    R2, #4          ; Right Index (Size 5 - 1)
	
	BL      my_MergeSort
	
	; 4. Load sorted values back into R0-R4 (Part 1 Requirement)
	LDR     R5, =Array_Data
	LDMIA   R5!, {R0-R4}
	
stop    B       stop

; R0: Array Base
; R1: Left Index
; R2: Right Index
my_MergeSort PROC
	; We push R0-R2 because we need to preserve the arguments (Base, Left, Right)
	; across the recursive calls. R3-R7 are saved to preserve context.
	PUSH    {R0-R7, LR}
	
	CMP     R1, R2
	BGE     ms_end
	
	; mid = (left + right) / 2
	ADDS    R3, R1, R2
	LSRS    R3, R3, #1
	
	; my_MergeSort(arr, left, mid)
	PUSH    {R2}            ; Save Right
	MOVS    R2, R3          ; Right = Mid
	BL      my_MergeSort
	POP     {R2}            ; Restore Right
	
	; my_MergeSort(arr, mid+1, right)
	PUSH    {R1}            ; Save Left
	MOVS    R1, R3          ; Mid
	ADDS    R1, R1, #1      ; Left = Mid + 1
	BL      my_MergeSort
	POP     {R1}            ; Restore Left
	
	; my_Merge(arr, left, mid, right)
	; Recalculate mid
	ADDS    R3, R1, R2
	LSRS    R3, R3, #1
	BL      my_Merge
	
ms_end
	POP     {R0-R7, PC}
	ENDP

; R0: Array Base
; R1: Left
; R2: Right
; R3: Mid
my_Merge PROC
	PUSH    {R0-R7, LR}
	
	; Local vars on stack: Mid, Right
	SUB     SP, #8
	STR     R3, [SP, #0]    ; Mid
	STR     R2, [SP, #4]    ; Right
	
	; R1 = i (Left)
	; R2 = j (Mid + 1)
	MOVS    R2, R3
	ADDS    R2, R2, #1
	
	; R3 = k (0)
	MOVS    R3, #0
	
	; R4 = Temp Base
	LDR     R4, =Temp_Arr
	
merge_loop
	; Check i > Mid
	LDR     R5, [SP, #0]
	CMP     R1, R5
	BGT     copy_j
	
	; Check j > Right
	LDR     R5, [SP, #4]
	CMP     R2, R5
	BGT     copy_i
	
	; Compare Arr[i], Arr[j]
	LSLS    R5, R1, #2
	LDR     R5, [R0, R5]    ; Arr[i]
	
	LSLS    R6, R2, #2
	LDR     R6, [R0, R6]    ; Arr[j]
	
	CMP     R5, R6
	BLE     take_i
	
take_j
	LSLS    R7, R3, #2
	STR     R6, [R4, R7]    ; Temp[k] = Arr[j]
	ADDS    R2, R2, #1
	ADDS    R3, R3, #1
	B       merge_loop
	
take_i
	LSLS    R7, R3, #2
	STR     R5, [R4, R7]    ; Temp[k] = Arr[i]
	ADDS    R1, R1, #1
	ADDS    R3, R3, #1
	B       merge_loop
	
copy_i
	LDR     R5, [SP, #0]    ; Mid
	CMP     R1, R5
	BGT     copy_back
	
	LSLS    R5, R1, #2
	LDR     R5, [R0, R5]
	LSLS    R6, R3, #2
	STR     R5, [R4, R6]
	ADDS    R1, R1, #1
	ADDS    R3, R3, #1
	B       copy_i
	
copy_j
	LDR     R5, [SP, #4]    ; Right
	CMP     R2, R5
	BGT     copy_back
	
	LSLS    R5, R2, #2
	LDR     R5, [R0, R5]
	LSLS    R6, R3, #2
	STR     R5, [R4, R6]
	ADDS    R2, R2, #1
	ADDS    R3, R3, #1
	B       copy_j
	
copy_back
	; Left = Right - k + 1
	LDR     R5, [SP, #4]    ; Right
	SUBS    R5, R5, R3      ; Right - k
	ADDS    R5, R5, #1      ; Left
	
	MOVS    R6, #0          ; Index for Temp
	
cb_loop
	CMP     R6, R3
	BGE     m_update_regs
	
	LSLS    R7, R6, #2
	LDR     R7, [R4, R7]    ; Load from Temp
	
	LSLS    R1, R5, #2
	STR     R7, [R0, R1]    ; Store to Arr
	
	ADDS    R6, R6, #1
	ADDS    R5, R5, #1
	B       cb_loop

m_update_regs
	; OPTIONAL: Load current array state into R0-R4 to visualize progress
	; This helps match the "gradual update" requirement in the debugger
	; Note: These values will be overwritten by POP in my_MergeSort, 
	; but you can see them here before returning.
	LDR     R0, [SP, #8]    ; Reload Base Address from Stack (R0 is at SP+8+0)
	LDMIA   R0, {R0-R4}     ; Load all 5 values
	
m_end
	ADD     SP, #8
	POP     {R0-R7, PC}
	ENDP

	AREA    MyData, DATA, READWRITE
	ALIGN
Array_Data  SPACE   20      ; Space for 5 words (5 * 4 bytes)
Temp_Arr    SPACE   20      ; Space for 5 words
	
	END