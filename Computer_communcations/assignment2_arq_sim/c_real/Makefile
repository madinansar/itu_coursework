CXX = g++
CXXFLAGS = -O3 -std=c++17 -pthread
TARGET = simulation

all: $(TARGET)

$(TARGET): main.cpp classes.hpp channel.hpp sender_improved.hpp receiver.hpp
	$(CXX) $(CXXFLAGS) main.cpp -o $(TARGET)

clean:
	rm -f $(TARGET)
