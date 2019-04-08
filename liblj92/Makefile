CFLAGS = -g -Wpointer-sign -Wpointer-sign -Wunused-variable -std=c99 -Wunused-but-set-variable

all: lj92test lj92enc lj92dec

lj92test: test.c lj92.c lj92.h
	gcc ${CFLAGS} lj92.c test.c -o lj92test -lm

lj92enc: encoder.c lj92.c lj92.h
	gcc ${CFLAGS} lj92.c encoder.c -o lj92enc

lj92dec: decoder.c lj92.c lj92.h
	gcc ${CFLAGS} lj92.c decoder.c -o lj92dec

clean:
	rm lj92test lj92enc lj92dec
