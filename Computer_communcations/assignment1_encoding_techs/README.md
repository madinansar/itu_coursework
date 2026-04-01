# Assignment 1 - Communication Systems Simulation

This project implements various communication encoding and modulation schemes (Digital-to-Digital, Digital-to-Analog, Analog-to-Digital, and Analog-to-Analog). It includes both command-line tools and a web-based interface to visualize the signal processing steps.

## 🚀 How to Run the Web Application

The web application consists of two parts: a backend **socket server** (Receiver/Server B) and a **Flask web app** (Sender/Client A + UI).

### Step 1: Start the Socket Server
Open a terminal and run the server. This mimics "Server B" which listens for incoming signals to decode/demodulate.
```bash
python3 server_B_web.py
```
*The server will start listening on `127.0.0.1:50007`.*

### Step 2: Start the Web App
Open a **new** terminal window (keep the server running) and launch the web interface.
```bash
python3 webapp_socket.py
```
*The Flask application will start, usually on `http://127.0.0.1:5000`.*

### Step 3: Use the Interface
1. Open your web browser and go to the URL shown in the terminal (e.g., `http://127.0.0.1:5000`).
2. Select a mode (D2D, D2A, A2D, A2A).
3. Enter input parameters (bits, frequency, etc.).
4. Click **"Send to Server"**.
5. The web app encodes the signal, sends it over the socket to the server, and displays the results (plots and decoded data).

---

## 📂 File Structure & Summaries

### Core Applications
| File | Description |
|------|-------------|
| **`webapp_socket.py`** | Flask web application serving the UI. Acts as "Client A" by encoding signals and sending them to `server_B_web.py` over a socket. |
| **`server_B_web.py`** | Socket server adapted for the web interface. Receives JSON-encoded signal data, processes (decodes) it, and prints the results. |
| **`main.py`** | Standalone Command Line Interface (CLI) tool to run all simulations locally without network sockets. Great for quick testing. |
| **`client_A.py`** | Original CLI-based socket client. Connects to `server_B.py`. |
| **`server_B.py`** | Original CLI-based socket server. |

### Signal Processing Libraries
| File | Description |
|------|-------------|
| **`digital2digital.py`** | Implements Line Coding schemes: **NRZ-L, NRZ-I, Manchester, AMI**. |
| **`digital2analog.py`** | Implements Modulation schemes: **ASK, FSK, BPSK**. |
| **`analog2digital.py`** | Implements PCM (Pulse Code Modulation) for converting analog signals to digital. |
| **`analog2analog.py`** | Implements Modulation schemes: **AM, FM, PM**. |

### Benchmarking & Utilities
| File | Description |
|------|-------------|
| **`benchmark_comprehensive.py`** | Performance testing script. Compares the "Original" user implementation against AI-optimized versions (Claude/Gemini) for speed and memory usage. |
| **`benchmark_results.csv`** | CSV file containing the raw output data from the benchmark runs. |
| **`ui.py`** | Helper module for CLI user input validation (e.g., ensuring bit strings only contain 0s and 1s). |
| **`ai_optimizations/`** | Folder containing vectorized, performance-optimized versions of the signal libraries used for benchmarking. |
| **`static/` & `templates/`** | Standard Flask folders for CSS/JS assets and HTML files. |
