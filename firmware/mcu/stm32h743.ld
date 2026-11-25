/* STM32H743 memory map: RM0433 §2.3 embedded SRAM, §3 embedded Flash.
 * 설계값: data/bss and 16 KiB stack in DTCM; AXI reserved for future buffers. */
ENTRY(Reset_Handler)
MEMORY {
 FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 2M
 DTCM (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
 AXI (rwx) : ORIGIN = 0x24000000, LENGTH = 512K
}
_estack = ORIGIN(DTCM) + LENGTH(DTCM);
SECTIONS {
 .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
 .text : { *(.text*) *(.rodata*) } > FLASH
 .ARM.extab : { *(.ARM.extab*) } > FLASH
 .ARM.exidx : { *(.ARM.exidx*) } > FLASH
 .data : { . = ALIGN(4); _sdata = .; *(.data*) . = ALIGN(4); _edata = .; } > DTCM AT> FLASH
 _sidata = LOADADDR(.data);
 .bss (NOLOAD) : { . = ALIGN(8); _sbss = .; *(.bss*) *(COMMON) . = ALIGN(8); _ebss = .; } > DTCM
 .axi (NOLOAD) : { *(.axi*) } > AXI
 /DISCARD/ : { *(.comment*) *(.note*) }
 ASSERT(_ebss <= _estack - 16K, "DTCM stack reserve exhausted")
}
