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

EMCC ?= emcc
NODE ?= node
WASM_EXPORTS = ['_fw_set_temp_period_ms','_fw_init','_fw_wasm_set_recipe','_fw_step_1ms','_fw_reset_latch','_fw_set_hw_fault','_fw_get_z_velocity','_fw_get_heater_power','_fw_get_mode','_fw_get_phase','_fw_get_warning','_fw_get_latched','_fw_get_brake','_fw_get_sto','_fw_get_force_setpoint','_fw_get_force_integral','_fw_get_temp_integral']
.PHONY: wasm test-wasm
wasm: build/controller.js build/controller.wasm

build/controller.js: Makefile $(CORE_SOURCES) hal/hal_wasm.c $(wildcard src/*.h hal/*.h)
	@mkdir -p build
	$(EMCC) $(CPPFLAGS) $(CFLAGS) -Dfw_step_1ms=fw_core_step_1ms $(CORE_SOURCES) hal/hal_wasm.c --no-entry -sMODULARIZE -sEXPORT_ES6 -sEXPORTED_FUNCTIONS="$(WASM_EXPORTS)" -sEXPORTED_RUNTIME_METHODS=cwrap,ccall -sALLOW_MEMORY_GROWTH=0 -sMALLOC=none -o $@

build/controller.wasm: build/controller.js
	@test -f $@ || { rm -f build/controller.js; $(MAKE) build/controller.js; }

build/test_fixed_inputs: $(SOURCES) $(wildcard src/*.h hal/*.h) test/test_fixed_inputs.c
	@mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SOURCES) test/test_fixed_inputs.c -lm -o $@

test-wasm: wasm build/test_fixed_inputs
	$(NODE) test/test_wasm.mjs
