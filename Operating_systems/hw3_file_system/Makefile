CC = gcc
CFLAGS = -Wall -Wextra -g
OBJS = fs.c utilities.c main.c
TARGET = minifs

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $(TARGET)

clean:
	rm -f $(TARGET) disk.img tests/output.txt

run: all
	chmod +x tests/commands.txt
	tee tests/output.txt < tests/commands.txt | while read -r cmd; do \
		echo "\$$ $${cmd}"; \
		eval "$${cmd}"; \
	done | tee -a tests/run_log.txt