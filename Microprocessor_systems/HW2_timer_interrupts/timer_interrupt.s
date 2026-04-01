STCTRL_ADDR     EQU 0xE000E010      ; SysTick Control and Status Register from datasheet
STRELOAD_ADDR   EQU 0xE000E014      ; SysTick Reload Value Register 
STCURR_ADDR     EQU 0xE000E018      ; SysTick Current Value Register
RELOAD_VAL      EQU 0x0098967F      ; 10,000,000 - 1 = 9 999 999 -> 0x0098967F

; -------------------------------------------------------------------------
; CODE AREA
; -------------------------------------------------------------------------
        AREA    |.text|, CODE, READONLY
        ALIGN   2
        THUMB
        EXPORT  __main
        
; -------------------------------------------------------------------------
; MAIN FUNCTION
; -------------------------------------------------------------------------
__main
        ; init
        LDR     R0, =STRELOAD_ADDR      ; R0 <- STRELOAD_ADDR
        LDR     R1, =RELOAD_VAL ; R1 <- RELOAD_VAL
        STR     R1, [R0]            ; update reload value: M[STRELOAD_ADDR] <- RELOAD_VAL
        
        LDR     R0, =STCURR_ADDR        ; R0 <- STCURR_ADDR
        MOVS     R1, #0  ; R1 <- 0
        STR     R1, [R0]            ; clear current value: M[STCURR_ADDR] <- 0
        
        LDR     R0, =STCTRL_ADDR        ; R0 <- STCTRL_ADDR
        MOVS     R1, #7              ; enable=1 | tickint=1 | clksource=1
        STR     R1, [R0]            ; start timer

wait_loop
        ; poll ready flag
        LDR     R0, =varb       ; R0 <- varb's address
wait_flag_check
        LDR     R1, [R0]        ; R1 <- M[varb]
        CMP     R1, #1  ; M[varb]==1 ?
        BNE     enter_sleep         ; if not 1, sleep
        B       process_input       ; if 1, process

enter_sleep
        WFI     ; Wait For Interrupt
        B       wait_flag_check ; recheck ready flag after waking up

process_input
        MOVS     R1, #0  ; R1 <- 0
        STR     R1, [R0]        ; varb = 0: clear flag

        LDR     R0, =var_inst   ; R0 <- address of var_inst
        LDR     R1, [R0]        ; R1 = Instruction from Handler

	PUSH {R1} ; save R1 temp
        ; go to next instruction:
        LDR     R0, =vari       ; R0 <- vari
        LDR     R1, [R0]        ; M[vari] <- R1
        ADDS     R1, R1, #1          ; increment index
        STR     R1, [R0]        ; save incremented value

	POP {R1}  ; get R1 back
        
        CMP     R1, #0xFF       ; check for end of array (==0xFF?)
        BEQ     stop_prog           ; end if 0xFF 

;decoding:
        MOVS     R0, R1              ; Copy to R0
        LSRS     R0, R0, #4          ; R0 = MSB (command)

; R1 = LSB (color/length)
        LSLS    R1, R1, #28     ; shift left by 28 (moves bottom 4 bits to top)
        LSRS    R1, R1, #28     ; shift right by 28 (moves them back, filling top with 0)

; execute:
        CMP     R0, #0xA            ; if MSB==A then change color
        BEQ     set_color       ; goto set_color

        CMP     R0, #3              ; if MSB<=3 then direction
        BLS     start_move      ; goto start_move

        B       wait_loop           ; else go to polling

set_color
        LDR     R0, =varc      ; get varc's address
        STRB    R1, [R0]            ; update varc variable
        B       wait_loop       ; go to polling

start_move
        ; R0 = direction, R1 = length
move_step
        CMP     R1, #0              ; if length is 0, done
        BEQ     wait_loop       ; go to polling
        
        PUSH    {R0, R1}            ; save state
        BL      update_pos_paint    ; goto update_pos_paint to make a move
        POP     {R0, R1}            ; restore state
        
        SUBS     R1, R1, #1          ; decrement length
        B       move_step       ; repeat moving until length is 0

stop_prog
        B       stop_prog           ; stop

; moves the cursor
update_pos_paint FUNCTION
        PUSH    {R0, R1, LR}        ; save registers to stack

        LDR     R1, =varx       ; get x coord's address
        LDR     R1, [R1]            ; update x: R1 = current x
        
        CMP     R0, #1              ; Right?
        BEQ     do_right        ; goto do_right
        CMP     R0, #3              ; Left?
        BEQ     do_left ; goto do_left
        B       check_x             ; Up/Down does not change x
        
do_right
        ADDS     R1, R1, #1      ; increments x (going right)
        B       check_x ; check the grid bounds
do_left
        SUBS     R1, R1, #1      ; decrements x (going left)

check_x
        CMP     R1, #31             ; check b bound (0-31) 
        BHI     skip_x              ; if invalid, don't save
        
        LDR     R0, =varx           ; reload address
        STR     R1, [R0]            ; save new x
skip_x
        LDR     R0, [SP, #0]        ; R0 = direction (restored from stack)

        LDR     R1, =vary       ; y coord's address
        LDR     R1, [R1]            ; R1 = current y

        CMP     R0, #0              ; Up?
        BEQ     do_up   ; goto do_up
        CMP     R0, #2              ; Down?
        BEQ     do_down ; goto do_down
        B       check_y             ; left/right does not change y

do_up
        SUBS     R1, R1, #1      ; decrement y (down)
        B       check_y ; check the grid bounds
do_down
        ADDS     R1, R1, #1      ; ; incremnet y (up)
        B       check_y ; check the grid bounds

check_y
        CMP     R1, #7              ; check y Bound (0-7) 
        BHI     skip_y              ; if invalid, don't save
        
        LDR     R0, =vary           ; reload address
        STR     R1, [R0]            ; save new y
skip_y

; painting:
        LDR     R0, =vary       ; get y coord's address
        LDR     R0, [R0]            ; R0 = y
        LSLS     R0, R0, #5          ; R0 = y * 32
        
        LDR     R1, =varx       ; get x coord's address
        LDR     R1, [R1]            ; R1 = X
        ADDS     R0, R0, R1          ; R0 = Offset
        
        LDR     R1, =0x20001000     ; base address
        ADDS     R0, R0, R1          ; R0 = pixel address
        
        LDR     R1, =varc      ; get varc's address
        LDRB    R1, [R1]            ; R1 = varc
        STRB    R1, [R0]            ; write to memory 

        POP     {R0, R1, PC}        ; restore
        ENDFUNC

; override handler:
SysTick_Handler FUNCTION
        EXPORT  SysTick_Handler     ; Export handler to override
        PUSH    {R0, R1, LR}        ; save registers  

        LDR     R0, =vari       ; fetch current array index
        LDR     R1, [R0]            ; R1 <- index

; getting the instruction(0xKK):
        LDR     R0, =arr            ; R0 <- array base
        LSLS     R1, R1, #2          ; offset = index * 4
        ADDS     R0, R0, R1          ; address of element
        LDR     R1, [R0]            ; R1 = instruction value 

        LDR     R0, =var_inst   ; get address of var_inst
        STR     R1, [R0]        ; store the instruction into memory

        LDR     R0, =varb ; get varb
        MOVS     R1, #1  ; R1 <- 1
        STR     R1, [R0]            ; Set varb

        POP     {R0, R1, PC}        ; restore
        ENDFUNC

; -------------------------------------------------------------------------
; DATA SECTION
; -------------------------------------------------------------------------

;Shorter Example
;---------------------------
;		AREA myData, DATA, READONLY ; Define a read only data section
;arr    	DCD 0xA8, 0x14, 0x24, 0x32, 0x02, 0xFF
;;		AREA myDataRW, DATA, READWRITE ; Define a read write data section
;varx    DCD 0 
;vary    DCD 0
;varc	DCB 0
;vari	DCD 0
;varb	DCD 0
;---------------------------
;Longer Example
;---------------------------
		AREA myData, DATA, READONLY ; Define a read only data section
arr    	DCD 0xA1, 0x15, 0x32, 0x27, 0x32, 0x14, 0xA0, 0x13, 0xA2, 0x11, 0x07, 0x32, 0x14, 0xA0, 0x11, 0xA3, 0x11, 0x27, 0x14, 0x07, 0xA0, 0x11, 0xA4, 0x14, 0x33, 0x27, 0x13, 0xA0, 0x11, 0xA5, 0x14, 0x03, 0x33, 0x04 , 0x13, 0xFF
		AREA myDataRW, DATA, READWRITE ; Define a read write data section
varx    DCD 0 
vary    DCD 0
varc	DCD 0
vari	DCD 0
varb	DCD 0
var_inst        DCD 0   ; variable for instruction
;----------------------------

        END