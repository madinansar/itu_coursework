CC = gcc
CFLAGS = -Wall -Wextra -pthread -g
TARGET = market_sim
SRC = 150220939_market_sim.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(TARGET)
