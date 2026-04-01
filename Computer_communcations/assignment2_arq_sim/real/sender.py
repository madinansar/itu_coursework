from classes import LinkFrame, TransportSegment

class LinkLayerSender:
    def __init__(self, window_size, timeout_interval):
        self.W = window_size
        self.timeout = timeout_interval
        
        # State Variables
        self.next_seq_num = 0       
        self.window_base = 0        
        
        # Buffers
        self.buffer = {} 
        self.timers = {} 
        
    def can_send(self):
        return len(self.buffer) < self.W

    def send_frame(self, data_segment, current_time):
        if not self.can_send():
            return None 

        seq = self.next_seq_num
        frame = LinkFrame(LinkFrame.DATA, seq, data_segment)
        
        # Buffer Frame and Start Timer
        self.buffer[seq] = frame
        self.timers[seq] = current_time + self.timeout
        
        self.next_seq_num += 1
        return frame

    def receive_ack(self, ack_seq):
        if ack_seq in self.buffer:
            # Clear from buffer and timer
            del self.buffer[ack_seq]
            del self.timers[ack_seq]
            
            # Slide Window Base
            if self.buffer:
                self.window_base = min(self.buffer.keys())
            else:
                self.window_base = self.next_seq_num

    def check_timeouts(self, current_time):
        retransmit_list = []
        
        for seq, expiry_time in self.timers.items():
            if current_time >= expiry_time:
                # Retransmit frame
                frame = self.buffer[seq]
                
                # Reset Timer
                self.timers[seq] = current_time + self.timeout
                
                retransmit_list.append(frame)
                
        return retransmit_list