.syntax unified
.cpu cortex-m7
.fpu fpv5-d16
.thumb
/* ARMv7-M ARM: exception vector table, SCB CPACR CP10/CP11.
 * STM32H743 RM0433 §12 interrupts: 150 external IRQ slots (0..149).
 * 설계값: unimplemented IRQs halt in Default_Handler. */
.section .isr_vector,"a",%progbits
.balign 1024
.word _estack, Reset_Handler
.word Default_Handler, Default_Handler, Default_Handler, Default_Handler
.word Default_Handler, 0, 0, 0, 0
.word Default_Handler, Default_Handler, 0, Default_Handler, SysTick_Handler
.rept 150
.word Default_Handler
.endr
.section .text.Reset_Handler,"ax",%progbits
.global Reset_Handler
.type Reset_Handler,%function
.thumb_func
Reset_Handler:
 /* Enable FPU before any hard-float C function. ARMv7-M ARM CPACR. */
 ldr r0, =0xE000ED88
 ldr r1, [r0]
 ldr r2, =0x00F00000
 orrs r1, r2
 str r1, [r0]
 dsb
 isb
 /* SCB VTOR: support debugger/startup with a non-default vector base. */
 ldr r0, =0xE000ED08
 ldr r1, =0x08000000
 str r1, [r0]
 ldr r0, =_sidata
 ldr r1, =_sdata
 ldr r2, =_edata
1: cmp r1, r2
 bcs 2f
 ldr r3, [r0], #4
 str r3, [r1], #4
 b 1b
2: ldr r1, =_sbss
 ldr r2, =_ebss
 movs r3, #0
3: cmp r1, r2
 bcs 4f
 str r3, [r1], #4
 b 3b
4: bl main
 b Default_Handler
.size Reset_Handler, .-Reset_Handler
.section .text.Default_Handler,"ax",%progbits
.global Default_Handler
.type Default_Handler,%function
.thumb_func
Default_Handler:
 b Default_Handler
.size Default_Handler, .-Default_Handler
