CC = cc
PYTHON ?= python3
CPPFLAGS = -Isrc -Ihal -Ibuild
CFLAGS = -std=c99 -Wall -Wextra -Werror -O2
SOURCES = src/fw.c src/force_ctrl.c src/temp_ctrl.c src/interlock.c src/sequencer.c hal/hal_host.c
.PHONY: test
test: build/test_force build/test_temp build/test_safety
	@status=0; ./build/test_force || status=1; \
	./build/test_temp || status=1; \
	./build/test_safety || status=1; exit $$status

build/golden_cases.h: test/load_golden.py ../sim/test/golden_vectors.json
	@mkdir -p build
	$(PYTHON) test/load_golden.py ../sim/test/golden_vectors.json $@

build/test_force: $(SOURCES) $(wildcard src/*.h hal/*.h) test/test_force.c build/golden_cases.h
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SOURCES) test/test_force.c -lm -o $@

build/golden_temp_cases.h: test/load_temp_golden.py ../sim/test/golden_vectors.json
	@mkdir -p build
	$(PYTHON) test/load_temp_golden.py ../sim/test/golden_vectors.json $@

build/test_temp: $(SOURCES) $(wildcard src/*.h hal/*.h) test/test_temp.c build/golden_temp_cases.h
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SOURCES) test/test_temp.c -lm -o $@

build/test_safety: $(SOURCES) $(wildcard src/*.h hal/*.h) test/test_safety.c
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SOURCES) test/test_safety.c -lm -o $@

CORE_SOURCES = $(filter-out hal/hal_host.c,$(SOURCES))
ARM_CC ?= arm-none-eabi-gcc
ARM_OBJCOPY ?= arm-none-eabi-objcopy
ARM_SIZE ?= arm-none-eabi-size
MCU_FLAGS = -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard -ffunction-sections -fdata-sections
.PHONY: mcu
mcu: build/controller.bin
	$(ARM_SIZE) build/controller.elf

build/controller.elf: $(CORE_SOURCES) hal/hal_stm32h7.c mcu/startup_stm32h743.s mcu/stm32h743.ld $(wildcard src/*.h hal/*.h)
	@mkdir -p build
	$(ARM_CC) $(CPPFLAGS) $(CFLAGS) $(MCU_FLAGS) $(CORE_SOURCES) hal/hal_stm32h7.c mcu/startup_stm32h743.s -nostartfiles -Wl,--gc-sections,-Map,build/controller.map -T mcu/stm32h743.ld -o $@

build/controller.bin: build/controller.elf
	$(ARM_OBJCOPY) -O binary $< $@
