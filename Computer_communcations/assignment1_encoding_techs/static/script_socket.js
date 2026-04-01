// Global variables
let currentMode = 'd2d';
let currentScheme = 'nrz-l';
let serverRunning = false;

// DOM elements
const modeSelect = document.getElementById('mode');
const schemeSelect = document.getElementById('scheme');
const sendBtn = document.getElementById('send-btn');
const receiverStatus = document.getElementById('receiver-status');
const serverStatusBanner = document.getElementById('server-status-banner');

// Check server status on page load
window.addEventListener('load', checkServerStatus);

// Check if server_B is running
async function checkServerStatus() {
    try {
        const response = await fetch('/check_server');
        const result = await response.json();
        
        serverRunning = result.running;
        
        if (result.running) {
            serverStatusBanner.style.background = '#d1fae5';
            serverStatusBanner.style.borderColor = '#10b981';
            serverStatusBanner.innerHTML = '<span style="color: #065f46; font-weight: 600;">Server B is running on port 50007 - Ready to communicate!</span>';
            sendBtn.disabled = false;
        } else {
            serverStatusBanner.style.background = '#fee2e2';
            serverStatusBanner.style.borderColor = '#ef4444';
            serverStatusBanner.innerHTML = `
                <span style="color: #991b1b; font-weight: 600;">Server B not running!</span><br>
                <span style="color: #7f1d1d; font-size: 0.9rem;">Please start server_B_web.py in a separate terminal first.</span>
            `;
            sendBtn.disabled = true;
        }
    } catch (error) {
        serverStatusBanner.style.background = '#fee2e2';
        serverStatusBanner.style.borderColor = '#ef4444';
        serverStatusBanner.innerHTML = '<span style="color: #991b1b; font-weight: 600;">Cannot check server status</span>';
        sendBtn.disabled = true;
    }
}

// Update UI based on selected mode
function updateUI() {
    currentMode = modeSelect.value;
    
    // Hide all parameter groups
    document.getElementById('encoding-scheme-group').style.display = 'block'; // Default show
    document.getElementById('a2a-scheme-group').style.display = 'none';
    
    document.getElementById('bits-group').style.display = 'none';
    document.getElementById('samples-group').style.display = 'none';
    document.getElementById('bitrate-group').style.display = 'none';
    document.getElementById('fs-group').style.display = 'none';
    document.getElementById('amplitude-group').style.display = 'none';
    document.getElementById('carrier-group').style.display = 'none';
    document.getElementById('signal-freq-group').style.display = 'none';
    document.getElementById('nbits-group').style.display = 'none';
    document.getElementById('message-freq-group').style.display = 'none';
    document.getElementById('mod-index-group').style.display = 'none';
    document.getElementById('freq-sens-group').style.display = 'none';
    document.getElementById('phase-sens-group').style.display = 'none';
    document.getElementById('duration-group').style.display = 'none';
    document.getElementById('sampling-rate-group').style.display = 'none';
    document.getElementById('freq-dev-group').style.display = 'none';
    
    // Update scheme options
    if (currentMode === 'd2d') {
        schemeSelect.innerHTML = `
            <option value="nrz-l">NRZ-L</option>
            <option value="nrz-i">NRZ-I</option>
            <option value="manchester">Manchester</option>
            <option value="ami">AMI</option>
        `;
        document.getElementById('bits-group').style.display = 'block';
        document.getElementById('samples-group').style.display = 'block';
        document.getElementById('amplitude-group').style.display = 'block';
        
    } else if (currentMode === 'd2a') {
        schemeSelect.innerHTML = `
            <option value="ask">ASK</option>
            <option value="fsk">FSK</option>
            <option value="bpsk">BPSK</option>
        `;
        document.getElementById('bits-group').style.display = 'block';
        document.getElementById('bitrate-group').style.display = 'block';
        document.getElementById('fs-group').style.display = 'block';
        document.getElementById('amplitude-group').style.display = 'block';
        document.getElementById('carrier-group').style.display = 'block';
        updateD2AParameters();
        
    } else if (currentMode === 'a2d') {
        schemeSelect.innerHTML = `<option value="pcm">PCM</option>`;
        document.getElementById('signal-freq-group').style.display = 'block';
        document.getElementById('nbits-group').style.display = 'block';
        document.getElementById('duration-group').style.display = 'block';
        document.getElementById('sampling-rate-group').style.display = 'block';
        
    } else if (currentMode === 'a2a') {
        document.getElementById('encoding-scheme-group').style.display = 'none'; // Hide general encoding scheme
        document.getElementById('a2a-scheme-group').style.display = 'block';
        
        document.getElementById('message-freq-group').style.display = 'block';
        document.getElementById('carrier-group').style.display = 'block';
        document.getElementById('duration-group').style.display = 'block';
        document.getElementById('sampling-rate-group').style.display = 'block';
        
        // Update A2A specific parameters based on selected scheme
        updateA2AParameters();
    }
    
    currentScheme = schemeSelect.value;
}

// Update A2A parameters based on selected modulation scheme
function updateA2AParameters() {
    const a2aScheme = document.getElementById('a2a_scheme').value;
    
    // Hide all scheme-specific parameters first
    document.getElementById('mod-index-group').style.display = 'none';
    document.getElementById('freq-sens-group').style.display = 'none';
    document.getElementById('phase-sens-group').style.display = 'none';
    
    // Show parameters based on selected scheme
    if (a2aScheme === 'am') {
        document.getElementById('mod-index-group').style.display = 'block';
    } else if (a2aScheme === 'fm') {
        document.getElementById('freq-sens-group').style.display = 'block';
    } else if (a2aScheme === 'pm') {
        document.getElementById('phase-sens-group').style.display = 'block';
    }
}

// Update D2A parameters based on selected modulation scheme
function updateD2AParameters() {
    if (modeSelect.value !== 'd2a') return;
    
    const d2aScheme = schemeSelect.value;
    const freqDevGroup = document.getElementById('freq-dev-group');
    
    if (d2aScheme === 'fsk') {
        freqDevGroup.style.display = 'block';
    } else {
        freqDevGroup.style.display = 'none';
    }
}

// Add event listener for A2A scheme changes
document.getElementById('a2a_scheme')?.addEventListener('change', updateA2AParameters);
schemeSelect.addEventListener('change', updateD2AParameters);

// Plot signal using Plotly
function plotSignal(elementId, time, signal, title, color = '#2563eb') {
    const trace = {
        x: time,
        y: signal,
        type: 'scatter',
        mode: 'lines',
        line: { color: color, width: 2 },
        name: title
    };
    
    const layout = {
        title: title,
        xaxis: { title: 'Time (s)' },
        yaxis: { title: 'Amplitude' },
        margin: { t: 40, r: 20, b: 40, l: 50 },
        height: 300
    };
    
    Plotly.newPlot(elementId, [trace], layout, {responsive: true});
}

// Plot multiple signals
function plotMultipleSignals(elementId, traces, title) {
    const layout = {
        title: title,
        xaxis: { title: 'Time (s)' },
        yaxis: { title: 'Amplitude' },
        margin: { t: 40, r: 20, b: 40, l: 50 },
        height: 300
    };
    
    Plotly.newPlot(elementId, traces, layout, {responsive: true});
}

// Send signal via socket
async function sendSignal() {
    if (!serverRunning) {
        alert('Server B is not running! Please start server_B_web.py first.');
        return;
    }
    
    try {
        sendBtn.disabled = true;
        sendBtn.textContent = 'Sending via Socket...';
        receiverStatus.textContent = 'Receiving data...';
        receiverStatus.style.color = '#f59e0b';
        
        currentMode = modeSelect.value;
        currentScheme = schemeSelect.value;
        
        let endpoint = '';
        let requestData = {
            scheme: currentScheme
        };
        
        // Gather parameters based on mode
        if (currentMode === 'd2d') {
            endpoint = '/send_d2d';
            requestData.bits = document.getElementById('bits').value;
            requestData.samples_per_bit = parseInt(document.getElementById('samples_per_bit').value);
            requestData.amplitude = parseFloat(document.getElementById('amplitude').value);
            
        } else if (currentMode === 'd2a') {
            endpoint = '/send_d2a';
            requestData.bits = document.getElementById('bits').value;
            requestData.bit_rate = parseFloat(document.getElementById('bit_rate').value);
            requestData.sampling_rate = parseInt(document.getElementById('fs').value);
            requestData.amplitude = parseFloat(document.getElementById('amplitude').value);
            requestData.carrier_freq = parseFloat(document.getElementById('carrier_freq').value);
            
            if (currentScheme === 'fsk') {
                requestData.freq_dev = parseFloat(document.getElementById('freq_dev').value);
            }
            
        } else if (currentMode === 'a2d') {
            endpoint = '/send_a2d';
            requestData.signal_freq = parseFloat(document.getElementById('signal_freq').value);
            requestData.n_bits = parseInt(document.getElementById('n_bits').value);
            requestData.duration = parseFloat(document.getElementById('duration').value);
            requestData.sampling_rate = parseInt(document.getElementById('sampling_rate').value);
            
        } else if (currentMode === 'a2a') {
            endpoint = '/send_a2a';
            const a2aScheme = document.getElementById('a2a_scheme').value;
            requestData.scheme = a2aScheme;
            requestData.message_freq = parseFloat(document.getElementById('message_freq').value);
            requestData.carrier_freq = parseFloat(document.getElementById('carrier_freq').value);
            requestData.duration = parseFloat(document.getElementById('duration').value);
            requestData.sampling_rate = parseInt(document.getElementById('sampling_rate').value);
            
            // Add scheme-specific parameters
            if (a2aScheme === 'am') {
                requestData.modulation_index = parseFloat(document.getElementById('modulation_index').value);
            } else if (a2aScheme === 'fm') {
                requestData.freq_sensitivity = parseFloat(document.getElementById('freq_sensitivity').value);
            } else if (a2aScheme === 'pm') {
                requestData.phase_sensitivity = parseFloat(document.getElementById('phase_sensitivity').value);
            }
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displaySenderResults(result.sent_data);
            displayReceiverResults(result.server_response);
            
            receiverStatus.textContent = 'Data received and decoded!';
            receiverStatus.style.color = '#16a34a';
        } else {
            alert('Error: ' + result.error);
            receiverStatus.textContent = 'Error: ' + result.error;
            receiverStatus.style.color = '#dc2626';
        }
        
    } catch (error) {
        alert('Communication error: ' + error.message);
        receiverStatus.textContent = 'Communication failed!';
        receiverStatus.style.color = '#dc2626';
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Encode & Send via Socket';
    }
}

// Display sender side results
function displaySenderResults(data) {
    if (currentMode === 'd2d' || currentMode === 'd2a') {
        plotSignal('sender-plot', data.time, data.signal,
                  `Sent Signal (${currentScheme.toUpperCase()}) via Port 50007`, '#2563eb');
        document.getElementById('sender-info').innerHTML = `
            <p><strong>Original Bits:</strong> ${data.original_bits}</p>
            <p><strong>Signal Samples:</strong> ${data.signal.length}</p>
            <p><strong>Transport:</strong> TCP Socket (Port 50007)</p>
        `;
        
    } else if (currentMode === 'a2d') {
        const traces = [
            {
                x: data.time,
                y: data.analog_signal,
                name: 'Original Analog',
                line: { color: '#2563eb', width: 2 }
            },
            {
                x: data.time,
                y: data.quantized_signal,
                name: 'Quantized',
                line: { color: '#dc2626', width: 2, dash: 'dot' }
            }
        ];
        plotMultipleSignals('sender-plot', traces, 'A2D: Quantization (Sent to Server B)');
        document.getElementById('sender-info').innerHTML = `
            <p><strong>Quantization Levels:</strong> ${Math.pow(2, data.n_bits)}</p>
            <p><strong>PCM Bits:</strong> ${data.pcm_bits.length} bits</p>
            <p><strong>Transport:</strong> TCP Socket (Port 50007)</p>
        `;
        
    } else if (currentMode === 'a2a') {
        const traces = [
            {
                x: data.time,
                y: data.message_signal,
                name: 'Message Signal',
                line: { color: '#2563eb', width: 2 }
            },
            {
                x: data.time,
                y: data.modulated_signal,
                name: 'Modulated (AM)',
                line: { color: '#dc2626', width: 1.5 }
            }
        ];
        plotMultipleSignals('sender-plot', traces, 'A2A: AM Modulation (Sent to Server B)');
        document.getElementById('sender-info').innerHTML = `
            <p><strong>Transport:</strong> TCP Socket (Port 50007)</p>
            <p><strong>Samples Sent:</strong> ${data.modulated_signal.length}</p>
        `;
    }
}

// Display receiver side results
function displayReceiverResults(response) {
    document.getElementById('receiver-info').style.display = 'block';
    document.getElementById('decoded-result').style.display = 'block';
    
    if (response.error) {
        document.getElementById('receiver-info').innerHTML = `
            <p style="color: #dc2626;"><strong>Error from Server B:</strong> ${response.error}</p>
        `;
        document.querySelector('.decoded-bits').textContent = 'Decoding failed';
        return;
    }
    
    if (currentMode === 'd2d') {
        const isMatch = response.match;
        document.getElementById('receiver-info').innerHTML = `
            <p><strong>Received via:</strong> TCP Socket (Port 50007)</p>
            <p><strong>Original Bits:</strong> ${response.original_bits}</p>
            <p><strong>Decoded Bits:</strong> ${response.decoded_bits}</p>
            <p><strong>Match:</strong> <span style="color: ${isMatch ? '#16a34a' : '#dc2626'}; font-weight: 600;">
                ${isMatch ? '✅ Perfect!' : '❌ Error detected'}
            </span></p>
        `;
        document.querySelector('.decoded-bits').textContent = response.decoded_bits;
        
    } else if (currentMode === 'd2a') {
        const isMatch = response.match;
        document.getElementById('receiver-info').innerHTML = `
            <p><strong>Received via:</strong> TCP Socket (Port 50007)</p>
            <p><strong>Original Bits:</strong> ${response.original_bits}</p>
            <p><strong>Recovered Bits:</strong> ${response.recovered_bits}</p>
            <p><strong>Match:</strong> <span style="color: ${isMatch ? '#16a34a' : '#dc2626'}; font-weight: 600;">
                ${isMatch ? '✅ Perfect!' : '❌ Error detected'}
            </span></p>
        `;
        document.querySelector('.decoded-bits').textContent = response.recovered_bits;
        
    } else if (currentMode === 'a2d') {
        document.getElementById('receiver-info').innerHTML = `
            <p><strong>Received via:</strong> TCP Socket (Port 50007)</p>
            <p><strong>Reconstructed Samples:</strong> ${response.samples}</p>
            <p><strong>Status:</strong> <span style="color: #16a34a; font-weight: 600;">✅ Decoded successfully</span></p>
        `;
        document.querySelector('.decoded-bits').textContent = `Reconstructed ${response.samples} samples from PCM`;
        
    } else if (currentMode === 'a2a') {
        document.getElementById('receiver-info').innerHTML = `
            <p><strong>Received via:</strong> TCP Socket (Port 50007)</p>
            <p><strong>Demodulated Samples:</strong> ${response.demodulated_signal.length}</p>
            <p><strong>Status:</strong> <span style="color: #16a34a; font-weight: 600;">✅ Demodulated successfully</span></p>
        `;
        document.querySelector('.decoded-bits').textContent = `Demodulated ${response.demodulated_signal.length} samples`;
    }
}

// Event listeners
modeSelect.addEventListener('change', updateUI);
schemeSelect.addEventListener('change', () => {
    currentScheme = schemeSelect.value;
});
sendBtn.addEventListener('click', sendSignal);

// Recheck server status every 5 seconds
setInterval(checkServerStatus, 5000);

// Initialize UI
updateUI();
