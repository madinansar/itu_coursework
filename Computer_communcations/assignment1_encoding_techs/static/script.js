// Global variables to store signal data
let currentSignalData = null;
let currentMode = 'd2d';
let currentScheme = 'nrz-l';

// DOM elements
const modeSelect = document.getElementById('mode');
const schemeSelect = document.getElementById('scheme');
const encodeBtn = document.getElementById('encode-btn');
const decodeBtn = document.getElementById('decode-btn');
const receiverStatus = document.getElementById('receiver-status');
const decodedResult = document.getElementById('decoded-result');

// Update UI based on selected mode
function updateUI() {
    currentMode = modeSelect.value;
    
    // Hide all parameter groups
    document.getElementById('bits-group').style.display = 'none';
    document.getElementById('samples-group').style.display = 'none';
    document.getElementById('amplitude-group').style.display = 'none';
    document.getElementById('carrier-group').style.display = 'none';
    document.getElementById('signal-freq-group').style.display = 'none';
    document.getElementById('nbits-group').style.display = 'none';
    document.getElementById('message-freq-group').style.display = 'none';
    document.getElementById('mod-index-group').style.display = 'none';
    document.getElementById('duration-group').style.display = 'none';
    document.getElementById('sampling-rate-group').style.display = 'none';
    
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
            <option value="ask">ASK (OOK)</option>
            <option value="fsk">FSK</option>
            <option value="bpsk">BPSK</option>
        `;
        document.getElementById('bits-group').style.display = 'block';
        document.getElementById('samples-group').style.display = 'block';
        document.getElementById('amplitude-group').style.display = 'block';
        document.getElementById('carrier-group').style.display = 'block';
        
    } else if (currentMode === 'a2d') {
        schemeSelect.innerHTML = `<option value="pcm">PCM</option>`;
        document.getElementById('signal-freq-group').style.display = 'block';
        document.getElementById('nbits-group').style.display = 'block';
        document.getElementById('duration-group').style.display = 'block';
        document.getElementById('sampling-rate-group').style.display = 'block';
        
    } else if (currentMode === 'a2a') {
        schemeSelect.innerHTML = `<option value="am">AM</option>`;
        document.getElementById('message-freq-group').style.display = 'block';
        document.getElementById('carrier-group').style.display = 'block';
        document.getElementById('mod-index-group').style.display = 'block';
        document.getElementById('duration-group').style.display = 'block';
        document.getElementById('sampling-rate-group').style.display = 'block';
    }
    
    currentScheme = schemeSelect.value;
}

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

// Encode and send signal
async function encodeSignal() {
    try {
        encodeBtn.disabled = true;
        encodeBtn.textContent = 'Encoding...';
        
        currentMode = modeSelect.value;
        currentScheme = schemeSelect.value;
        
        const requestData = {
            mode: currentMode,
            scheme: currentScheme
        };
        
        // Gather parameters based on mode
        if (currentMode === 'd2d' || currentMode === 'd2a') {
            requestData.bits = document.getElementById('bits').value;
            requestData.samples_per_bit = parseInt(document.getElementById('samples_per_bit').value);
            requestData.amplitude = parseFloat(document.getElementById('amplitude').value);
            
            if (currentMode === 'd2a') {
                requestData.carrier_freq = parseFloat(document.getElementById('carrier_freq').value);
            }
            
        } else if (currentMode === 'a2d') {
            requestData.signal_freq = parseFloat(document.getElementById('signal_freq').value);
            requestData.n_bits = parseInt(document.getElementById('n_bits').value);
            requestData.duration = parseFloat(document.getElementById('duration').value);
            requestData.sampling_rate = parseInt(document.getElementById('sampling_rate').value);
            
        } else if (currentMode === 'a2a') {
            requestData.message_freq = parseFloat(document.getElementById('message_freq').value);
            requestData.carrier_freq = parseFloat(document.getElementById('carrier_freq').value);
            requestData.modulation_index = parseFloat(document.getElementById('modulation_index').value);
            requestData.duration = parseFloat(document.getElementById('duration').value);
            requestData.sampling_rate = parseInt(document.getElementById('sampling_rate').value);
        }
        
        const response = await fetch('/encode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentSignalData = result;
            
            // Plot based on mode
            if (currentMode === 'd2d' || currentMode === 'd2a') {
                plotSignal('sender-plot', result.time, result.signal, 
                          `Encoded Signal (${currentScheme.toUpperCase()})`, '#2563eb');
                document.getElementById('sender-info').innerHTML = `
                    <p><strong>Original Bits:</strong> ${result.original_bits}</p>
                    <p><strong>Signal Samples:</strong> ${result.signal.length}</p>
                `;
                
            } else if (currentMode === 'a2d') {
                const traces = [
                    {
                        x: result.time,
                        y: result.analog_signal,
                        name: 'Original Analog',
                        line: { color: '#2563eb', width: 2 }
                    },
                    {
                        x: result.time,
                        y: result.quantized_signal,
                        name: 'Quantized',
                        line: { color: '#dc2626', width: 2, dash: 'dot' }
                    }
                ];
                plotMultipleSignals('sender-plot', traces, 'A2D: Quantization');
                document.getElementById('sender-info').innerHTML = `
                    <p><strong>Quantization Levels:</strong> ${Math.pow(2, result.n_bits)}</p>
                    <p><strong>PCM Bits:</strong> ${result.pcm_bits.length} bits</p>
                    <p><strong>Bit String:</strong> ${result.pcm_bits.substring(0, 64)}${result.pcm_bits.length > 64 ? '...' : ''}</p>
                `;
                
            } else if (currentMode === 'a2a') {
                const traces = [
                    {
                        x: result.time,
                        y: result.message_signal,
                        name: 'Message Signal',
                        line: { color: '#2563eb', width: 2 }
                    },
                    {
                        x: result.time,
                        y: result.modulated_signal,
                        name: 'Modulated (AM)',
                        line: { color: '#dc2626', width: 1.5 }
                    }
                ];
                plotMultipleSignals('sender-plot', traces, 'A2A: AM Modulation');
                document.getElementById('sender-info').innerHTML = `
                    <p><strong>Message Freq:</strong> ${requestData.message_freq} Hz</p>
                    <p><strong>Carrier Freq:</strong> ${requestData.carrier_freq} Hz</p>
                    <p><strong>Modulation Index:</strong> ${requestData.modulation_index}</p>
                `;
            }
            
            // Enable receiver
            receiverStatus.textContent = 'Signal received! Ready to decode.';
            receiverStatus.style.color = '#16a34a';
            decodeBtn.disabled = false;
            
        } else {
            alert('Encoding failed: ' + result.error);
        }
        
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        encodeBtn.disabled = false;
        encodeBtn.textContent = 'Encode & Send';
    }
}

// Decode received signal
async function decodeSignal() {
    if (!currentSignalData) {
        alert('No signal to decode!');
        return;
    }
    
    try {
        decodeBtn.disabled = true;
        decodeBtn.textContent = 'Decoding...';
        
        const requestData = {
            mode: currentMode,
            scheme: currentScheme
        };
        
        // Prepare decode request based on mode
        if (currentMode === 'd2d' || currentMode === 'd2a') {
            requestData.signal = currentSignalData.signal;
            requestData.samples_per_bit = parseInt(document.getElementById('samples_per_bit').value);
            requestData.amplitude = parseFloat(document.getElementById('amplitude').value);
            
            if (currentMode === 'd2a') {
                requestData.carrier_freq = parseFloat(document.getElementById('carrier_freq').value);
            }
            
        } else if (currentMode === 'a2d') {
            requestData.pcm_bits = currentSignalData.pcm_bits;
            requestData.n_bits = parseInt(document.getElementById('n_bits').value);
            
        } else if (currentMode === 'a2a') {
            requestData.signal = currentSignalData.modulated_signal;
            requestData.carrier_freq = parseFloat(document.getElementById('carrier_freq').value);
            requestData.sampling_rate = parseInt(document.getElementById('sampling_rate').value);
        }
        
        const response = await fetch('/decode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Display decoded result
            if (currentMode === 'd2d' || currentMode === 'd2a') {
                const isMatch = result.decoded_bits === currentSignalData.original_bits;
                document.getElementById('receiver-info').innerHTML = `
                    <p><strong>Original:</strong> ${currentSignalData.original_bits}</p>
                    <p><strong>Decoded:</strong> ${result.decoded_bits}</p>
                    <p><strong>Match:</strong> <span style="color: ${isMatch ? '#16a34a' : '#dc2626'}">
                        ${isMatch ? '✓ Perfect!' : '✗ Error detected'}
                    </span></p>
                `;
                
                // Plot received signal
                plotSignal('receiver-plot', currentSignalData.time, currentSignalData.signal,
                          'Received Signal', '#dc2626');
                
            } else if (currentMode === 'a2d') {
                const traces = [
                    {
                        x: currentSignalData.time,
                        y: currentSignalData.analog_signal,
                        name: 'Original',
                        line: { color: '#2563eb', width: 2 }
                    },
                    {
                        x: currentSignalData.time,
                        y: result.reconstructed_signal,
                        name: 'Reconstructed',
                        line: { color: '#16a34a', width: 2, dash: 'dot' }
                    }
                ];
                plotMultipleSignals('receiver-plot', traces, 'A2D: Reconstructed Signal');
                document.getElementById('receiver-info').innerHTML = `
                    <p><strong>Reconstruction complete!</strong></p>
                    <p>Quantization bits: ${currentSignalData.n_bits}</p>
                `;
                
            } else if (currentMode === 'a2a') {
                const traces = [
                    {
                        x: currentSignalData.time,
                        y: currentSignalData.message_signal,
                        name: 'Original Message',
                        line: { color: '#2563eb', width: 2 }
                    },
                    {
                        x: currentSignalData.time,
                        y: result.demodulated_signal,
                        name: 'Demodulated',
                        line: { color: '#16a34a', width: 2, dash: 'dot' }
                    }
                ];
                plotMultipleSignals('receiver-plot', traces, 'A2A: Demodulated Signal');
                document.getElementById('receiver-info').innerHTML = `
                    <p><strong>Demodulation complete!</strong></p>
                `;
            }
            
            decodedResult.style.display = 'block';
            
        } else {
            alert('Decoding failed: ' + result.error);
        }
        
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        decodeBtn.disabled = false;
        decodeBtn.textContent = 'Decode Signal';
    }
}

// Event listeners
modeSelect.addEventListener('change', updateUI);
schemeSelect.addEventListener('change', () => {
    currentScheme = schemeSelect.value;
});
encodeBtn.addEventListener('click', encodeSignal);
decodeBtn.addEventListener('click', decodeSignal);

// Initialize UI
updateUI();
