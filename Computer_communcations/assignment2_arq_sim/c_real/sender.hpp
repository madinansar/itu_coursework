#ifndef SENDER_HPP
#define SENDER_HPP

#include "classes.hpp"
#include <map>
#include <vector>
#include <algorithm>
#include <cmath>      
#include <limits>     

class LinkLayerSender {
public:
    int W;

    double timeout;

    int next_seq_num;
    int window_base;

    std::map<int, LinkFrame> buffer;         
    std::map<int, double> timers;            
    std::map<int, double> first_send_times;  

    std::map<int, int> retransmit_count;

    // Stats
    double total_rtt_sum;
    long long rtt_count;

    // Adaptive timeout variables 
    double srtt;       
    double rttvar;     
    double rto;        

    const double alpha = 0.125;
    const double beta  = 0.25;

    const double RTO_MIN = 0.010;  
    const double RTO_MAX = 10.0;   

    LinkLayerSender(int w, double t)
        : W(w), timeout(t), next_seq_num(0), window_base(0),
          total_rtt_sum(0.0), rtt_count(0),
          srtt(t), rttvar(t / 2.0), rto(t) {}

    bool can_send() const {
        return buffer.size() < (size_t)W;
    }

    // Creates frame and returns true if successful, putting result in out_frame
    bool send_frame(const TransportSegment& data_segment, double current_time, LinkFrame& out_frame) {
        if (!can_send()) {
            return false;
        }

        int seq = next_seq_num;
        out_frame = LinkFrame(LinkFrame::DATA, seq, data_segment);

        buffer[seq] = out_frame;
        retransmit_count[seq] = 0;
        timers[seq] = current_time + rto;
        first_send_times[seq] = current_time;
        next_seq_num++;

        return true;
    }

    void receive_ack(int ack_seq, double current_time) {
        if (!buffer.count(ack_seq)) {
            return;
        }

        if (retransmit_count.count(ack_seq) && retransmit_count[ack_seq] == 0) {
            if (first_send_times.count(ack_seq)) {
                double sample_rtt = current_time - first_send_times[ack_seq];

                rttvar = (1.0 - beta) * rttvar + beta * std::abs(srtt - sample_rtt);
                srtt   = (1.0 - alpha) * srtt + alpha * sample_rtt;
                rto    = srtt + 4.0 * rttvar;

                if (rto < RTO_MIN) rto = RTO_MIN;
                if (rto > RTO_MAX) rto = RTO_MAX;

                total_rtt_sum += sample_rtt;
                rtt_count++;

                first_send_times.erase(ack_seq);
            }
        } else {
            first_send_times.erase(ack_seq);
        }

        buffer.erase(ack_seq);
        timers.erase(ack_seq);
        retransmit_count.erase(ack_seq);
        first_send_times.erase(ack_seq);

        if (!buffer.empty()) {
            window_base = buffer.begin()->first;
        } else {
            window_base = next_seq_num;
        }
    }

    std::vector<LinkFrame> check_timeouts(double current_time) {
        std::vector<LinkFrame> retransmit_list;

        for (auto& pair : timers) {
            int seq = pair.first;
            double expiry_time = pair.second;

            if (current_time >= expiry_time) {
                if (buffer.count(seq)) {
                    retransmit_list.push_back(buffer[seq]);
                }

                first_send_times.erase(seq);
                retransmit_count[seq]++;

                // Aggressive recovery: No exponential backoff. Just retry at RTO.
                double next_wait = rto; 

                if (next_wait > RTO_MAX) next_wait = RTO_MAX;
                if (next_wait < RTO_MIN) next_wait = RTO_MIN;

                timers[seq] = current_time + next_wait;
            }
        }

        return retransmit_list;
    }
};

#endif
