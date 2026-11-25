CC = cc
CPPFLAGS = -Isrc -Ihal
CFLAGS = -std=c99 -Wall -Wextra -Werror -O2
SOURCES = src/fw.c src/force_ctrl.c hal/hal_host.c
.PHONY: test
test:
	$(CC) $(CPPFLAGS) $(CFLAGS) -fsyntax-only $(SOURCES)
