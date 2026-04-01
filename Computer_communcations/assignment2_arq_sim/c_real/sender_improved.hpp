#ifndef SENDER_HPP
#define SENDER_HPP

#include "classes.hpp"
#include <map>
#include <vector>
#include <algorithm>
#include <cmath>      // std::abs
#include <limits>     // (optional)

class LinkLayerSender {
public:
    int W;

    // Keep the original timeout as the initial value (baseline)
    double timeout;

    int next_seq_num;
    int window_base;

    std::map<int, LinkFrame> buffer;         // Buffers sent frames
    std::map<int, double> timers;            // Expiry time for each frame
    std::map<int, double> first_send_times;  // First send time (for RTT samples)

    // Track retransmissions per seq (needed for Karn's rule + backoff)
    std::map<int, int> retransmit_count;

    // Stats
    double total_rtt_sum;
    long long rtt_count;

    // Adaptive timeout variables (Jacobson/Karels)
    double srtt;       // Smoothed RTT
    double rttvar;     // RTT variation
    double rto;        // Retransmission timeout (adaptive)

    const double alpha = 0.125;
    const double beta  = 0.25;

    // RTO bounds (keep reasonable, avoids insane values)
    const double RTO_MIN = 0.010;  // 10 ms (Standard)
    const double RTO_MAX = 10.0;   // 10  s

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

        // 1) Create frame
        out_frame = LinkFrame(LinkFrame::DATA, seq, data_segment);

        // 2) Buffer it
        buffer[seq] = out_frame;

        // 3) Initialize retransmit count for this new seq
        retransmit_count[seq] = 0;

        // 4) Start adaptive timer using current RTO
        timers[seq] = current_time + rto;

        // 5) Track first send time (ONLY for first transmission)
        first_send_times[seq] = current_time;

        // 6) Advance seq
        next_seq_num++;

        return true;
    }

    void receive_ack(int ack_seq, double current_time) {
        if (!buffer.count(ack_seq)) {
            return;
        }

        // --- Adaptive RTT update (Karn's rule) ---
        // Only update RTT if this frame was NEVER retransmitted
        if (retransmit_count.count(ack_seq) && retransmit_count[ack_seq] == 0) {
            if (first_send_times.count(ack_seq)) {
                double sample_rtt = current_time - first_send_times[ack_seq];

                // Jacobson/Karels:
                // rttvar = (1-beta)*rttvar + beta*|srtt - sample|
                // srtt   = (1-alpha)*srtt + alpha*sample
                rttvar = (1.0 - beta) * rttvar + beta * std::abs(srtt - sample_rtt);
                srtt   = (1.0 - alpha) * srtt + alpha * sample_rtt;
                rto    = srtt + 4.0 * rttvar;

                // Clamp RTO
                if (rto < RTO_MIN) rto = RTO_MIN;
                if (rto > RTO_MAX) rto = RTO_MAX;

                // Keep your stats (avg RTT)
                total_rtt_sum += sample_rtt;
                rtt_count++;

                first_send_times.erase(ack_seq);
            }
        } else {
            // If retransmitted, do NOT use RTT sample (Karn)
            first_send_times.erase(ack_seq);
        }

        // 1) Remove from buffer and clear timer
        buffer.erase(ack_seq);
        timers.erase(ack_seq);
        retransmit_count.erase(ack_seq);
        first_send_times.erase(ack_seq);

        // 2) Slide Window Base
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
                // If the frame is still buffered, retransmit it
                if (buffer.count(seq)) {
                    retransmit_list.push_back(buffer[seq]);
                }

                // Karn: discard first_send_time so ACK won't update RTT incorrectly
                first_send_times.erase(seq);

                // Mark retransmission
                retransmit_count[seq]++;

                // Backoff: increase timeout for this seq to prevent retry storms
                // Simple exponential: rto * 2^k (clamped)
                // MODIFIED: Reduced backoff aggressiveness to improve goodput on lossy links
                // Instead of 2^k, use constant or linear, or just RTO.
                int k = retransmit_count[seq];
                // double backoff_factor = std::pow(2.0, std::min(k, 10)); 
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
