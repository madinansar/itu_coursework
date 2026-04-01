#ifndef RECEIVER_HPP
#define RECEIVER_HPP

#include "classes.hpp"
#include <map>
#include <vector>

class LinkLayerReceiver {
public:
    int expected_seq_num;       // The next Sequence # we are waiting for to deliver to App
    std::map<int, TransportSegment> buffer;                // Buffer for out-of-order frames { seq_num: payload }
    long long total_delivered_bytes;        
    
    LinkLayerReceiver() : expected_seq_num(0), total_delivered_bytes(0) {}

    // Process incoming frame.
    // Returns true if an ACK is generated (written to out_ack).
    // Returns false if corrupted or ignored.
    bool receive_frame(LinkFrame& frame, LinkFrame& out_ack) {
        if (frame.corrupted) {
            return false; 
        }

        if (frame.type != LinkFrame::DATA) {
            return false;
        }

        int seq = frame.seq_num;
        
        // Duplicate Detection
        if (seq < expected_seq_num) {
            out_ack = LinkFrame(LinkFrame::ACK, seq);
            return true;
        }

        // Out-of-Order Handling
        if (seq == expected_seq_num) {
            _deliver_data(frame.payload);
            expected_seq_num++;
            
            // Check Buffer for subsequent frames
            while (buffer.count(expected_seq_num)) {
                _deliver_data(buffer[expected_seq_num]);
                buffer.erase(expected_seq_num); // pop
                expected_seq_num++;
            }
        } else {
            // Future frame -> Buffer it
            if (buffer.find(seq) == buffer.end()) {
                buffer[seq] = frame.payload;
            }
        }
        
        // Send ACK
        out_ack = LinkFrame(LinkFrame::ACK, seq);
        return true;
    }

private:
    void _deliver_data(const TransportSegment& transport_segment) {
        if (transport_segment.payload_size > 0) {
            total_delivered_bytes += transport_segment.payload_size;
        }
    }
};

#endif
