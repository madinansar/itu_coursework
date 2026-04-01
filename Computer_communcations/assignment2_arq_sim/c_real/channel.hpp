#ifndef CHANNEL_HPP
#define CHANNEL_HPP

#include <random>
#include <cmath>

class GilbertElliotChannel {
    double p_g = 1e-6;          
    double p_b = 5e-3;          
    double trans_g_to_b = 0.002;
    double trans_b_to_g = 0.05;
    
    enum State { GOOD, BAD };
    State current_state;
    std::mt19937 rng;
    long long total_bits_good;
    long long total_bits_bad;

public:
    GilbertElliotChannel(int seed) : current_state(GOOD), total_bits_good(0), total_bits_bad(0) {
        rng.seed(seed);
    }
    
    double get_bad_state_fraction() const {
        long long total = total_bits_good + total_bits_bad;
        if (total == 0) return 0.0;
        return (double)total_bits_bad / total;
    }

    void update_state() {
        std::uniform_real_distribution<> dis(0.0, 1.0);
        double roll = dis(rng);
        
        if (current_state == GOOD) {
            if (roll < trans_g_to_b) {
                current_state = BAD;
            }
        } else { 
            if (roll < trans_b_to_g) {
                current_state = GOOD;
            }
        }
    }

    bool is_packet_corrupted(int packet_len_bytes) {
        long long bits_remaining = (long long)packet_len_bytes * 8;
        double log_prob_no_error = 0.0; 

        double prob_no_error = 1.0;

        std::geometric_distribution<long long> dist_g_to_b(trans_g_to_b);
        std::geometric_distribution<long long> dist_b_to_g(trans_b_to_g);

        while (bits_remaining > 0) {
            long long bits_until_switch;
            double current_ber;

            if (current_state == GOOD) {
                bits_until_switch = dist_g_to_b(rng);
                current_ber = p_g;
            } else {
                bits_until_switch = dist_b_to_g(rng);
                current_ber = p_b;
            }

            long long bits_in_chunk = std::min(bits_remaining, bits_until_switch);

            if (current_state == GOOD) total_bits_good += bits_in_chunk;
            else total_bits_bad += bits_in_chunk;
            
            prob_no_error *= std::pow(1.0 - current_ber, bits_in_chunk);
            
            bits_remaining -= bits_in_chunk;

            if (bits_remaining > 0) {
                current_state = (current_state == GOOD) ? BAD : GOOD;
            }
        }
        
        std::uniform_real_distribution<> dis(0.0, 1.0);
        return dis(rng) > prob_no_error; 
    }
};

#endif
