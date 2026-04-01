#ifndef CLASSES_HPP
#define CLASSES_HPP

#include <vector>
#include <string>

class TransportSegment {
public:
    static const int HEADER_SIZE = 8;
    int seq_num;
    int payload_size; // Storing size instead of actual 'x's
    double timestamp;

    TransportSegment(int seq, int size) : seq_num(seq), payload_size(size), timestamp(0.0) {}
    TransportSegment() : seq_num(0), payload_size(0), timestamp(0.0) {}

    int size_bytes() const {
        return HEADER_SIZE + payload_size;
    }
};

class LinkFrame {
public:
    static const int HEADER_SIZE = 24;
    enum Type { DATA, ACK, NACK };
    
    Type type;
    int seq_num;
    TransportSegment payload;
    bool has_payload;
    double send_time;
    bool corrupted;

    // Constructor for DATA with payload
    LinkFrame(Type t, int seq, const TransportSegment& p) 
        : type(t), seq_num(seq), payload(p), has_payload(true), send_time(0.0), corrupted(false) {}
    
    // Constructor for ACK/Control without payload
    LinkFrame(Type t, int seq) 
        : type(t), seq_num(seq), has_payload(false), send_time(0.0), corrupted(false) {}

    // Default constructor
    LinkFrame() : type(DATA), seq_num(0), has_payload(false), send_time(0.0), corrupted(false) {}

    int size_bytes() const {
        int payload_size = has_payload ? payload.size_bytes() : 0;
        return HEADER_SIZE + payload_size;
    }

    long long size_bits() const {
        return (long long)size_bytes() * 8;
    }
};

#endif
