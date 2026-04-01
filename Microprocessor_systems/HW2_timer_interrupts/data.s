---------------------------
Shorter Example
---------------------------
		AREA myData, DATA, READONLY ; Define a read only data section
arr    	DCD 0xA8, 0x14, 0x24, 0x32, 0x02, 0xFF
		AREA myDataRW, DATA, READWRITE ; Define a read write data section
varx    DCD 0 
vary    DCD 0
varc	DCB 0
vari	DCD 0
varb	DCD 0
---------------------------
Longer Example
---------------------------
		AREA myData, DATA, READONLY ; Define a read only data section
arr    	DCD 0xA1, 0x15, 0x32, 0x27, 0x32, 0x14, 0xA0, 0x13, 0xA2, 0x11, 0x07, 0x32, 0x14, 0xA0, 0x11, 0xA3, 0x11, 0x27, 0x14, 0x07, 0xA0, 0x11, 0xA4, 0x14, 0x33, 0x27, 0x13, 0xA0, 0x11, 0xA5, 0x14, 0x03, 0x33, 0x04 , 0x13, 0xFF
		AREA myDataRW, DATA, READWRITE ; Define a read write data section
varx    DCD 0 
vary    DCD 0
varc	DCB 0
vari	DCD 0
varb	DCD 0
----------------------------



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
varc	DCB 0
vari	DCD 0
varb	DCD 0
;----------------------------