import time

class TransportSegment:
    HEADER_SIZE = 8

    def __init__(self, seq_num, payload_size=0):
        self.seq_num = seq_num
        self.payload_size = payload_size
        self.timestamp = 0.0

    @property
    def size_bytes(self):
        return self.HEADER_SIZE + self.payload_size

    def __repr__(self):
        return f"Seg(Seq={self.seq_num}, Size={self.size_bytes})"


class LinkFrame:
    HEADER_SIZE = 24
    
    # Frame Types
    DATA = 'DATA'
    ACK = 'ACK'
    NACK = 'NACK'

    def __init__(self, frame_type, seq_num, payload_segment=None):
        self.type = frame_type
        self.seq_num = seq_num # For DATA, this is the ID. For ACK, this is the ID being ACKed.
        self.payload = payload_segment # The TransportSegment object
        
        # Simulation metadata
        self.send_time = 0.0
        self.corrupted = False

    @property
    def size_bits(self):
        return self.size_bytes * 8

    @property
    def size_bytes(self):
        payload_size = self.payload.size_bytes if self.payload else 0
        return self.HEADER_SIZE + payload_size

    def __repr__(self):
        status = " [CORRUPT]" if self.corrupted else ""
        if self.type == self.DATA:
            return f"Frame[DATA](Seq={self.seq_num}, Payload={self.payload.size_bytes}B){status}"
        else:
            return f"Frame[{self.type}](Seq={self.seq_num}){status}"
