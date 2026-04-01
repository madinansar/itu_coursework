import heapq
import csv
import random
import os
import time
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm  

from classes import TransportSegment
from channel import GilbertElliotChannel
from sender import LinkLayerSender
from receiver import LinkLayerReceiver

# CONFIGURATION
QUICK_MODE = False  
FILE_SIZE_BYTES = 100 * 1024 * 1024 
MAX_TIME_LIMIT = 20.0 if QUICK_MODE else 6000.0 

W_VALUES = [2, 4, 8, 16, 32, 64]
L_VALUES = [128, 256, 512, 1024, 2048, 4096]
SEEDS = range(10) 

# Physical Constants
BIT_RATE = 10e6
PROP_DELAY_FWD = 0.040
PROP_DELAY_REV = 0.010
PROC_DELAY = 0.002

# EVENTS
EVT_SEND_READY = "SEND_READY"
EVT_FRAME_ARRIVAL = "FRAME_ARRIVAL"
EVT_ACK_ARRIVAL = "ACK_ARRIVAL"
EVT_TIMEOUT_CHECK = "TIMEOUT_CHECK"

class Event:
    def __init__(self, time, type, data=None):
        self.time = time
        self.type = type
        self.data = data
    def __lt__(self, other):
        return self.time < other.time

class Simulator:
    def __init__(self, W, L, seed):
        random.seed(seed) 
        self.W = W
        self.L = L
        self.current_time = 0.0
        self.event_queue = []
        
        self.channel = GilbertElliotChannel()
        self.sender = LinkLayerSender(window_size=W, timeout_interval=0.200) 
        self.receiver = LinkLayerReceiver()
        
        self.generated_packets = 0
        self.sender_busy_until = 0.0
        self.retransmissions = 0
        self.total_delivered_bytes = 0
        
        self.app_data_size = L - TransportSegment.HEADER_SIZE 

    def schedule(self, delay, type, data=None):
        heapq.heappush(self.event_queue, Event(self.current_time + delay, type, data))

    def run(self):
        self.schedule(0.0, EVT_SEND_READY)
        self.schedule(0.01, EVT_TIMEOUT_CHECK)

        while self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            if self.current_time > MAX_TIME_LIMIT:
                break
            
            if self.receiver.total_delivered_bytes >= FILE_SIZE_BYTES:
                break

            if event.type == EVT_SEND_READY:
                self.handle_send()
            elif event.type == EVT_FRAME_ARRIVAL:
                self.handle_arrival(event.data)
            elif event.type == EVT_ACK_ARRIVAL:
                self.handle_ack(event.data)
            elif event.type == EVT_TIMEOUT_CHECK:
                self.handle_timeout()
                self.schedule(0.01, EVT_TIMEOUT_CHECK)

        return self.get_stats()

    def handle_send(self):
        if self.current_time < self.sender_busy_until:
            self.schedule(self.sender_busy_until - self.current_time, EVT_SEND_READY)
            return

        while self.sender.can_send():
            current_generated_bytes = self.generated_packets * self.app_data_size
            if current_generated_bytes >= FILE_SIZE_BYTES:
                break

            seg = TransportSegment(self.generated_packets, self.app_data_size)
            frame = self.sender.send_frame(seg, self.current_time)
            
            if frame:
                self.generated_packets += 1
                self.transmit_frame(frame)
            else:
                break

    def transmit_frame(self, frame):
        ser_delay = frame.size_bits / BIT_RATE
        
        start_time = max(self.current_time, self.sender_busy_until)
        self.sender_busy_until = start_time + ser_delay
        transit_time = self.sender_busy_until + PROP_DELAY_FWD + PROC_DELAY
        
        self.schedule(transit_time - self.current_time, EVT_FRAME_ARRIVAL, frame)
        self.schedule(self.sender_busy_until - self.current_time, EVT_SEND_READY)

    def handle_arrival(self, frame):
        frame.corrupted = self.channel.is_packet_corrupted(frame.size_bytes)
        ack = self.receiver.receive_frame(frame)
        if ack:
            ser_delay = ack.size_bits / BIT_RATE
            transit = ser_delay + PROP_DELAY_REV + PROC_DELAY
            self.schedule(transit, EVT_ACK_ARRIVAL, ack)

    def handle_ack(self, ack):
        if not self.channel.is_packet_corrupted(ack.size_bytes):
            self.sender.receive_ack(ack.seq_num)
            self.schedule(0.0, EVT_SEND_READY)

    def handle_timeout(self):
        retrans = self.sender.check_timeouts(self.current_time)
        if retrans:
            self.retransmissions += len(retrans)
            for frame in retrans:
                self.transmit_frame(frame)

    def get_stats(self):
        self.total_delivered_bytes = self.receiver.total_delivered_bytes
        
        goodput_mbps = 0
        if self.current_time > 0:
            goodput_mbps = (self.total_delivered_bytes * 8) / (self.current_time * 1e6)
            
        return {
            "W": self.W, 
            "L": self.L, 
            "Goodput": goodput_mbps,
            "Retransmissions": self.retransmissions,
            "Duration": self.current_time,
            "BadStateFraction": self.channel.get_bad_state_fraction()
        }

if __name__ == "__main__":
    CSV_FILE = "simulation_results.csv"
    
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["W", "L", "Seed", "Goodput_Mbps", "Retransmissions", "Duration_Sec", "BadStateFraction"])

    total_runs = len(W_VALUES) * len(L_VALUES) * len(SEEDS)
    
    print(f"Starting Simulation Sweep...")
    print(f"Quick Mode: {QUICK_MODE}")
    print(f"Total Runs: {total_runs}")
    print("-" * 60)

    results_buffer = []
    
    with tqdm(total=total_runs, unit="run") as pbar:
        for W in W_VALUES:
            for L in L_VALUES:
                for seed in SEEDS:
                    sim = Simulator(W, L, seed)
                    res = sim.run()
                    
                    with open(CSV_FILE, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([res["W"], res["L"], seed, res["Goodput"], res["Retransmissions"], res["Duration"], res["BadStateFraction"]])
                    
                    pbar.update(1)
                    
                    res['Seed'] = seed
                    results_buffer.append(res)
                    
                    # Log to CSV
                    with open(CSV_FILE, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([W, L, seed, res['Goodput'], res['Retransmissions'], res['Duration'], res['BadStateFraction']])
                    
                    # Update Progress Bar with current stats
                    pbar.set_postfix({
                        "W": W, 
                        "L": L, 
                        "Gput": f"{res['Goodput']:.2f}M"
                    })
                    pbar.update(1)

    print("\n" + "-" * 60)
    print("Generating Heatmap...")
    
    df = pd.DataFrame(results_buffer)
    heatmap_data = df.groupby(['W', 'L'])['Goodput'].mean().unstack().sort_index(ascending=False)

    plt.figure(figsize=(10, 8))
    sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="viridis", 
                cbar_kws={'label': 'Goodput (Mbps)'})
    
    plt.title("Simulated Goodput (Mbps) - Selective Repeat ARQ")
    plt.xlabel("Frame Payload Size (L) [Bytes]")
    plt.ylabel("Window Size (W)")
    plt.savefig("goodput_heatmap.png")
    print("Heatmap saved to 'goodput_heatmap.png'")
    # plt.show() # Commented out so it doesn't block if running on headless server