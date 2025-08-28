CC = gcc
CFLAGS = -O3 -Wall -Wextra -fPIC -I../
LDFLAGS = -shared -lm

SRCS = pixatool_engine.c pixatool_wrapper.c
OBJS = $(SRCS:.c=.o)
TARGET = libpixatool.so

# Platform-specific settings
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    TARGET = libpixatool.dylib
    LDFLAGS = -dynamiclib -lm
endif
ifeq ($(UNAME_S),Linux)
    CFLAGS += -D_GNU_SOURCE
endif

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $@ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

test: $(TARGET)
	$(CC) -o test_pixatool test_pixatool.c -L. -lpixatool -lm -Wl,-rpath,.
	./test_pixatool

install: $(TARGET)
	cp $(TARGET) ../../lib/