from classes import LinkFrame

class LinkLayerReceiver:
    def __init__(self):
        self.expected_seq_num = 0       # Next expected Sequence ID
        self.buffer = {}                # Buffer for out-of-order frames
        self.total_delivered_bytes = 0  # Bytes delivered to App Layer
        
    def receive_frame(self, frame):
        # 1. Check for Corruption
        if frame.corrupted:
            return None

        # 2. Check Frame Type
        if frame.type != LinkFrame.DATA:
            return None

        seq = frame.seq_num
        
        # 3. Duplicate Detection
        if seq < self.expected_seq_num:
            return LinkFrame(LinkFrame.ACK, seq)

        # 4. Out-of-Order Handling
        if seq == self.expected_seq_num:
            self._deliver_data(frame.payload)
            self.expected_seq_num += 1
            
            # Process Buffer
            while self.expected_seq_num in self.buffer:
                queued_payload = self.buffer.pop(self.expected_seq_num)
                self._deliver_data(queued_payload)
                self.expected_seq_num += 1
        else:
            # Buffer Future Frame
            if seq not in self.buffer:
                self.buffer[seq] = frame.payload
        
        # 5. Send ACK
        return LinkFrame(LinkFrame.ACK, seq)

    def _deliver_data(self, transport_segment):
        # Passes data to Application Layer
        if transport_segment.payload_size > 0:
            self.total_delivered_bytes += transport_segment.payload_size