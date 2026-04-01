import random
import math

class GilbertElliotChannel:
    def __init__(self):
        # Channel parameters
        self.p_g = 1e-6          # Good state BER
        self.p_b = 5e-3          # Bad state BER
        self.trans_g_to_b = 0.002
        self.trans_b_to_g = 0.05
        
        self.current_state = 'GOOD'
        
        # Stats
        self.total_bits_good = 0
        self.total_bits_bad = 0

    def get_geometric_sample(self, p):
        # Geometric distribution sampling
        # Returns number of failures before first success
        if p >= 1.0: return 0
        u = random.random()
        if u <= 0.0: u = 1e-10
        if u >= 1.0: u = 1.0 - 1e-10
        
        return math.floor(math.log(u) / math.log(1.0 - p))

    def is_packet_corrupted(self, packet_len_bytes):
        # Determines packet corruption using bit-level simulation
        bits_remaining = packet_len_bytes * 8
        prob_no_error = 1.0
        
        while bits_remaining > 0:
            if self.current_state == 'GOOD':
                bits_until_switch = self.get_geometric_sample(self.trans_g_to_b)
                current_ber = self.p_g
            else:
                bits_until_switch = self.get_geometric_sample(self.trans_b_to_g)
                current_ber = self.p_b
                
            bits_in_chunk = min(bits_remaining, bits_until_switch)
            
            # Stats tracking
            if self.current_state == 'GOOD':
                self.total_bits_good += bits_in_chunk
            else:
                self.total_bits_bad += bits_in_chunk
            
            # P(No Error in chunk) = (1 - BER)^bits
            prob_no_error *= pow(1.0 - current_ber, bits_in_chunk)
            
            bits_remaining -= bits_in_chunk
            
            # Transition state if period ends
            if bits_remaining > 0:
                self.current_state = 'BAD' if self.current_state == 'GOOD' else 'GOOD'
        
        return random.random() > prob_no_error

    def get_bad_state_fraction(self):
        total = self.total_bits_good + self.total_bits_bad
        if total == 0: return 0.0
        return self.total_bits_bad / total
