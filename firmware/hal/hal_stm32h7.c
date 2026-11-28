#include <stdint.h>
#include "hal.h"
#include "fw.h"
#define REG32(a) (*(volatile uint32_t *)(a))
/* RM0433 §8 RCC registers: CR, CFGR, D1CFGR and AHB4ENR.
 * 설계값: HSI 64 MHz, HSIDIV=/1, SYSCLK=HSI; D1/AHB/APB reset /1.
 * No PLL or overclock. This startup assumes hardware reset (no bootloader). */
#define RCC_CR REG32(0x58024400u)
#define RCC_CFGR REG32(0x58024410u)
#define RCC_D1CFGR REG32(0x58024418u)
#define RCC_AHB4ENR REG32(0x580244E0u)
/* RM0433 §11 GPIO registers MODER/PUPDR/IDR, GPIOG base.
 * 설계값: PG0 active-high fault, pull-down; provisional pin, board bring-up TODO.
 * External comparator/latch must cut power independently (10장 10.4절). */
#define GPIOG_MODER REG32(0x58021800u)
#define GPIOG_PUPDR REG32(0x5802180Cu)
#define GPIOG_IDR REG32(0x58021810u)
/* ARMv7-M ARM SysTick CTRL/LOAD/VAL, processor clock source. */
#define SYST_CSR REG32(0xE000E010u)
#define SYST_RVR REG32(0xE000E014u)
#define SYST_CVR REG32(0xE000E018u)
#define CORE_CLOCK_HZ 64000000u /* RM0433 §8 HSI nominal 64 MHz, 설계값 /1. */
#define TICK_HZ 1000u /* HANDOFF §2 / fw_config.h: 설계값 1 ms scheduler. */
static void clock_gpio_init(void)
{
    RCC_CR |= 1u; /* HSION */
    while (!(RCC_CR & (1u << 2))) { } /* HSIRDY */
    RCC_CR &= ~(3u << 3); /* HSIDIV /1 */
    RCC_CFGR &= ~7u; /* SW=HSI */
    while (RCC_CFGR & (7u << 3)) { } /* SWS=HSI */
    RCC_D1CFGR = 0u;
    RCC_AHB4ENR |= 1u << 6; /* GPIOGEN */
    (void)RCC_AHB4ENR;
    GPIOG_MODER &= ~3u;
    GPIOG_PUPDR = (GPIOG_PUPDR & ~3u) | 2u;
}
void SysTick_Handler(void) { fw_step_1ms(); }
int main(void)
{
    clock_gpio_init();
    fw_init();
    /* 64,000,000 / 1000 - 1 = 63,999; ARM SysTick counts LOAD..0. */
    SYST_RVR = CORE_CLOCK_HZ / TICK_HZ - 1u;
    SYST_CVR = 0u;
    SYST_CSR = 7u; /* ENABLE | TICKINT | CLKSOURCE */
    for (;;) __asm volatile ("wfi");
}
float hal_read_force_N(void)
{
    /* TODO(board bring-up): ADS1256 SPI conversion and calibration. */
    return 0.0f;
}
float hal_read_temp_C(void)
{
    /* TODO(board bring-up): AD8495 internal ADC conversion and calibration. */
    return 0.0f;
}
int hal_hw_fault(void) { return (GPIOG_IDR & 1u) != 0u; }
void hal_write_z_velocity_mm_s(float v)
{
    /* TODO(board bring-up): servo command interface. */
    (void)v;
}
void hal_write_heater_W(float p)
{
    /* TODO(board bring-up): 20 kHz PWM, duty=P/400 (HANDOFF §3.2). */
    (void)p;
}
void hal_write_reflow_heater_W(float p)
{
    /* 배선 설계값 PE11 TIM1 CH2, HAL 미구현.
     * TODO(board bring-up): PWM duty=P/FW_REFLOW_HEATER_MAX_W. */
    (void)p;
}
void hal_write_safety(int brake, int sto)
{
    /* TODO(board bring-up): status outputs; not the independent hardware cutoff. */
    (void)brake; (void)sto;
}
