#include <iostream>
#include <queue>
#include <vector>
#include <cmath>
#include <fstream>
#include <thread>
#include <mutex>
#include <atomic>
#include <chrono>
#include <tuple>
#include <algorithm>
#include <iomanip>

#include "classes.hpp"
#include "channel.hpp"
#include "sender.hpp"
#include "sender_improved.hpp"
#include "receiver.hpp"

// --- CONFIGURATION ---
const bool QUICK_MODE = false;
const long long FILE_SIZE_BYTES = 100LL * 1024 * 1024; // Back to 100MB
const double MAX_TIME_LIMIT = 60000.0; 

// Physical Constants
const double BIT_RATE = 10e6;
const double PROP_DELAY_FWD = 0.040;
const double PROP_DELAY_REV = 0.010;
const double PROC_DELAY = 0.002;

// --- EVENTS ---
enum EventType { 
    EVT_SEND_READY, 
    EVT_FRAME_ARRIVAL, 
    EVT_ACK_ARRIVAL, 
    EVT_TIMEOUT_CHECK 
};

struct Event {
    double time;
    EventType type;
    LinkFrame frame_data; // Only valid if type is ARRIVAL
    bool has_frame;

    Event(double t, EventType ty) : time(t), type(ty), has_frame(false) {}
    Event(double t, EventType ty, const LinkFrame& f) : time(t), type(ty), frame_data(f), has_frame(true) {}

    // Priority Queue is max-heap by default, so we invert logic for min-heap (smallest time first)
    bool operator>(const Event& other) const {
        return time > other.time;
    }
};

struct SimulationResult {
    int W;
    int L;
    int Seed;
    double Goodput;
    long long Retransmissions;
    double AvgRTT;
    double Utilization;
    long long BufferEvents;
};

class Simulator {
    int W;
    int L;
    int seed;
    
    double current_time;
    std::priority_queue<Event, std::vector<Event>, std::greater<Event>> event_queue;
    
    GilbertElliotChannel channel;
    LinkLayerSender sender;
    LinkLayerReceiver receiver;
    
    long long generated_packets;
    double sender_busy_until;
    long long retransmissions;
    long long total_delivered_bytes;
    int app_data_size;

    // Stats
    double total_busy_time;
    long long buffer_events;

public:
    Simulator(int w, int l, int s) 
        : W(w), L(l), seed(s), current_time(0.0), channel(s), sender(w, 0.200),
          generated_packets(0), sender_busy_until(0.0), retransmissions(0), total_delivered_bytes(0),
          total_busy_time(0.0), buffer_events(0)
    {
        app_data_size = L - TransportSegment::HEADER_SIZE;
    }

    void schedule(double delay, EventType type) {
        event_queue.push(Event(current_time + delay, type));
    }

    void schedule(double delay, EventType type, const LinkFrame& frame) {
        event_queue.push(Event(current_time + delay, type, frame));
    }

    SimulationResult run() {
        schedule(0.0, EVT_SEND_READY);
        schedule(0.01, EVT_TIMEOUT_CHECK);

        while (!event_queue.empty()) {
            Event event = event_queue.top();
            event_queue.pop();
            current_time = event.time;
            
            // Fix: Check receiver's count directly
            if (current_time > MAX_TIME_LIMIT) break;
            if (receiver.total_delivered_bytes >= FILE_SIZE_BYTES) break;

            if (event.type == EVT_SEND_READY) {
                handle_send();
            } else if (event.type == EVT_FRAME_ARRIVAL) {
                if (event.has_frame) handle_arrival(event.frame_data);
            } else if (event.type == EVT_ACK_ARRIVAL) {
                if (event.has_frame) handle_ack(event.frame_data);
            } else if (event.type == EVT_TIMEOUT_CHECK) {
                handle_timeout();
                // Schedule next timeout check
                schedule(0.01, EVT_TIMEOUT_CHECK);
            }
        }

        return get_stats();
    }

    void handle_send() {
        if (current_time < sender_busy_until) {
            schedule(sender_busy_until - current_time, EVT_SEND_READY);
            return;
        }

        while (sender.can_send()) {
            long long current_generated_bytes = generated_packets * app_data_size;
            if (current_generated_bytes >= FILE_SIZE_BYTES) {
                break;
            }

            TransportSegment seg((int)generated_packets, app_data_size);
            LinkFrame frame;
            
            if (sender.send_frame(seg, current_time, frame)) {
                generated_packets++;
                transmit_frame(frame);
            } else {
                break;
            }
        }
        
        // Check for buffer event (Window Full)
        long long current_generated_bytes = generated_packets * app_data_size;
        if (!sender.can_send() && current_generated_bytes < FILE_SIZE_BYTES) {
            buffer_events++;
        }
    }

    void transmit_frame(const LinkFrame& frame) {
        double ser_delay = frame.size_bits() / BIT_RATE;
        total_busy_time += ser_delay; // Track busy time
        
        double start_time = std::max(current_time, sender_busy_until);
        sender_busy_until = start_time + ser_delay;
        
        double transit_time = sender_busy_until + PROP_DELAY_FWD + PROC_DELAY;
        
        // Schedule Arrival
        schedule(transit_time - current_time, EVT_FRAME_ARRIVAL, frame);
        
        // Schedule ready for next transmission
        schedule(sender_busy_until - current_time, EVT_SEND_READY);
    }

    void handle_arrival(LinkFrame frame) {
        // frame passed by value, so we can modify it (corrupted flag) locally
        frame.corrupted = channel.is_packet_corrupted(frame.size_bytes());
        
        LinkFrame ack;
        bool ack_generated = receiver.receive_frame(frame, ack);
        
        if (ack_generated) {
            double ser_delay = ack.size_bits() / BIT_RATE;
            double transit = ser_delay + PROP_DELAY_REV + PROC_DELAY;
            schedule(transit, EVT_ACK_ARRIVAL, ack);
        }
    }

    void handle_ack(LinkFrame ack) {
        // Ack also subject to channel errors? Python code:
        // if not self.channel.is_packet_corrupted(ack.size_bytes):
        if (!channel.is_packet_corrupted(ack.size_bytes())) {
            sender.receive_ack(ack.seq_num, current_time);
            // Check if we can send more immediately
            schedule(0.0, EVT_SEND_READY);
        }
    }

    void handle_timeout() {
        std::vector<LinkFrame> retrans = sender.check_timeouts(current_time);
        if (!retrans.empty()) {
            retransmissions += retrans.size();
            for (const auto& frame : retrans) {
                transmit_frame(frame);
            }
        }
    }

    SimulationResult get_stats() {
        total_delivered_bytes = receiver.total_delivered_bytes;
        
        double goodput_mbps = 0;
        double avg_rtt = 0;
        double utilization = 0;

        if (current_time > 0) {
            goodput_mbps = (total_delivered_bytes * 8.0) / (current_time * 1e6);
            utilization = total_busy_time / current_time;
        }

        if (sender.rtt_count > 0) {
            avg_rtt = sender.total_rtt_sum / sender.rtt_count;
        }
            
        return {W, L, seed, goodput_mbps, retransmissions, avg_rtt, utilization, buffer_events};
    }
};

// --- PARALLEL EXECUTION ---

std::mutex results_mutex;
std::vector<SimulationResult> global_results;

void worker_thread(std::vector<std::tuple<int, int, int>> tasks, std::atomic<int>& progress) {
    for (const auto& task : tasks) {
        int W = std::get<0>(task);
        int L = std::get<1>(task);
        int seed = std::get<2>(task);
        
        // Skip W=64, L=4096
        if (W == 64 && L == 4096) {
            {
                std::lock_guard<std::mutex> lock(results_mutex);
                // W, L, Seed, Goodput, Retransmissions, AvgRTT, Utilization, BufferEvents
                global_results.push_back({W, L, seed, 0.0, 0, 0.0, 0.0, 0});
            }
            progress++;
            continue;
        }

        Simulator sim(W, L, seed);
        SimulationResult res = sim.run();
        
        {
            std::lock_guard<std::mutex> lock(results_mutex);
            global_results.push_back(res);
        }
        
        progress++;
    }
}

int main() {
    // Parameter Space
    // std::vector<int> W_VALUES = {2, 4, 8, 16, 32, 64};
    // std::vector<int> L_VALUES = {128, 256, 512, 1024, 2048, 4096};
    std::vector<int> W_VALUES = {64};
    std::vector<int> L_VALUES = {512};
    
    std::vector<int> SEEDS;
    for(int i=0; i<10; ++i) SEEDS.push_back(i);

    // Prepare Task List
    std::vector<std::tuple<int, int, int>> tasks;
    for (int W : W_VALUES) {
        for (int L : L_VALUES) {
            for (int seed : SEEDS) {
                tasks.push_back({W, L, seed});
            }
        }
    }

    int total_runs = tasks.size();
    unsigned int num_threads = std::thread::hardware_concurrency();
    if (num_threads == 0) num_threads = 4;
    // Leave some breathing room if needed, but for CPU bound tasks match cores
    if (num_threads > 2) num_threads -= 1; 

    std::cout << "Starting Simulation Sweep" << std::endl;
    std::cout << "Parallel Workers: " << num_threads << std::endl;
    std::cout << "Total Runs: " << total_runs << std::endl;
    std::cout << "------------------------------------------------------------" << std::endl;

    // Distribute tasks
    std::vector<std::vector<std::tuple<int, int, int>>> thread_tasks(num_threads);
    for (size_t i = 0; i < tasks.size(); ++i) {
        thread_tasks[i % num_threads].push_back(tasks[i]);
    }

    std::atomic<int> progress(0);
    std::vector<std::thread> threads;
    
    // Start threads
    auto start_time = std::chrono::high_resolution_clock::now();
    
    for (unsigned int i = 0; i < num_threads; ++i) {
        threads.emplace_back(worker_thread, thread_tasks[i], std::ref(progress));
    }

    // Monitor progress
    while (progress < total_runs) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
        int p = progress;
        float percent = (float)p / total_runs * 100.0f;
        
        // Peek at latest result for status (unsafe read but fine for display)
        std::string status = "";
        {
            // Just grab the last result if available
            std::lock_guard<std::mutex> lock(results_mutex);
            if (!global_results.empty()) {
                const auto& last = global_results.back();
                status = " [Last: W=" + std::to_string(last.W) + 
                         " L=" + std::to_string(last.L) + 
                         " GPut=" + std::to_string(last.Goodput).substr(0,4) + "M]";
            }
        }
        
        std::cout << "\rProgress: " << p << "/" << total_runs << " (" 
                  << std::fixed << std::setprecision(1) << percent << "%)" 
                  << status << std::string(10, ' ') << std::flush;
    }
    
    // Join
    for (auto& t : threads) {
        t.join();
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end_time - start_time;

    std::cout << "\n------------------------------------------------------------" << std::endl;
    std::cout << "Simulation Complete in " << elapsed.count() << " seconds." << std::endl;

    // Write CSV
    std::ofstream csv("simulation_results_optimized_512_64.csv");
    csv << "W,L,run id,goodput,retransmissions,avg RTT,utilization,buffer events\n";
    for (const auto& r : global_results) {
        csv << r.W << "," << r.L << "," << r.Seed << "," 
            << r.Goodput << "," << r.Retransmissions << "," << r.AvgRTT << "," << r.Utilization << "," << r.BufferEvents << "\n";
    }
    csv.close();
    std::cout << "Results saved to simulation_results.csv" << std::endl;

    return 0;
}
