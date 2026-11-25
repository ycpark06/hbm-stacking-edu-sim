CC = cc
PYTHON ?= python3
CPPFLAGS = -Isrc -Ihal -Ibuild
CFLAGS = -std=c99 -Wall -Wextra -Werror -O2
SOURCES = src/fw.c src/force_ctrl.c src/temp_ctrl.c hal/hal_host.c
.PHONY: test
test: build/test_force build/test_temp
	./build/test_force
	./build/test_temp

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
