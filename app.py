import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write, read
from scipy.signal import butter, lfilter, firwin, freqz
from scipy import signal
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, ttk
import os

# Parámetros de grabación
fs = 24000  # Frecuencia de muestreo de 24 KHz (múltiplo de 8 KHz)
duration = 10  # Duración de 10 segundos para cada vocal

# Función para grabar una señal de audio
def check_or_record_audio(filename):
    if os.path.exists(filename):
        print(f"Archivo {filename} encontrado. Cargando...")
        sample_rate, audio = read(filename)
        if sample_rate != fs:
            print(f"Advertencia: La frecuencia de muestreo del archivo {filename} es {sample_rate} Hz, no {fs} Hz como se esperaba.")
        return audio
    else:
        print(f"Grabando {filename}...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Esperar hasta que termine la grabación
        write(filename, fs, audio)  # Guardar la señal grabada en un archivo
        return audio

# Función para aplicar un filtro pasa banda
def improved_bandpass_filter(data, lowcut, highcut, fs, order=6):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = signal.butter(order, [low, high], btype='band', output='sos')
    filtered_data = signal.sosfilt(sos, data)
    return filtered_data

# Función para graficar el espectro
def plot_spectrum(signal, fs, title):
    n = len(signal)
    k = np.arange(n)
    T = n / fs
    frq = k / T
    frq = frq[range(n//2)]
    Y = np.fft.fft(signal) / n
    Y = Y[range(n//2)]
    
    plt.plot(frq, abs(Y))
    plt.title(title)
    plt.xlabel('Frecuencia (Hz)')
    plt.ylabel('Amplitud')
    plt.show()

def modulate(signal, fc, fs):
    t = np.arange(len(signal)) / fs
    carrier = np.cos(2 * np.pi * fc * t)
    return signal * carrier

def demodulate(signal, fc, fs):
    t = np.arange(len(signal)) / fs
    carrier = np.cos(2 * np.pi * fc * t)
    demodulated = signal * carrier
    return improved_bandpass_filter(demodulated, 300, 3400, fs)

# Intercalar valores nulos entre los valores de la señal para elevar la frecuencia de muestreo
def upsample(signal, factor):
    upsampled = np.zeros(len(signal) * factor)
    upsampled[::factor] = signal
    return upsampled

# Función para demultiplexar una señal
def demultiplex(signal, factor, length):
    return signal[::factor][:length]

def ensure_minimum_length(signal, min_length):
    if len(signal) < min_length:
        padding = min_length - len(signal)
        return np.pad(signal, (0, padding), 'constant')
    return signal

def process_signals():
    global a_signal, e_signal, i_signal, processed_a, processed_e, processed_i

    if a_signal is None or e_signal is None or i_signal is None:
        messagebox.showerror("Error", "Debe grabar todas las señales primero.")
        return

    # 1. Apply bandpass filter to limit the signal to 300 Hz - 3.4 kHz
    lowcut = 300.0
    highcut = 3400.0
    a_filtered = improved_bandpass_filter(a_signal, lowcut, highcut, fs)
    e_filtered = improved_bandpass_filter(e_signal, lowcut, highcut, fs)
    i_filtered = improved_bandpass_filter(i_signal, lowcut, highcut, fs)

    # 2. Reduce sampling rate to 8 kHz
    fs_new = 8000
    decimation_factor = int(fs / fs_new)
    
    # Design a low-pass filter for decimation
    nyq = 0.5 * fs
    cutoff = fs_new / 2
    N, beta = signal.kaiserord(60, width=(fs_new/2)/nyq)
    taps = signal.firwin(N, cutoff, window=('kaiser', beta), scale=True, nyq=nyq)

    # Resample and apply the low-pass filter
    a_resampled = signal.resample_poly(a_filtered, 1, decimation_factor, window=taps)
    e_resampled = signal.resample_poly(e_filtered, 1, decimation_factor, window=taps)
    i_resampled = signal.resample_poly(i_filtered, 1, decimation_factor, window=taps)

    # 3. Convert to 8-bit representation
    a_resampled_8bit = np.int8(a_resampled / np.max(np.abs(a_resampled)) * 127)
    e_resampled_8bit = np.int8(e_resampled / np.max(np.abs(e_resampled)) * 127)
    i_resampled_8bit = np.int8(i_resampled / np.max(np.abs(i_resampled)) * 127)

    # 4. Plot spectra of original and processed signals
    plot_spectrum(a_signal, fs, 'Espectro de la señal original "a"')
    plot_spectrum(a_resampled_8bit, fs_new, 'Espectro de la señal acondicionada "a"')
    plot_spectrum(e_signal, fs, 'Espectro de la señal original "e"')
    plot_spectrum(e_resampled_8bit, fs_new, 'Espectro de la señal acondicionada "e"')
    plot_spectrum(i_signal, fs, 'Espectro de la señal original "i"')
    plot_spectrum(i_resampled_8bit, fs_new, 'Espectro de la señal acondicionada "i"')

    # 5. Implement multiplexing
    # Define carrier frequencies for each channel
    fc1, fc2, fc3 = 60000, 64000, 68000  # Carrier frequencies

    # Upsample the signals to the multiplexed sampling rate
    fs_multiplexed = 192000  # Example: 24 times the base rate of 8000 Hz
    upsample_factor = fs_multiplexed // fs_new
    
    a_upsampled = np.repeat(a_resampled_8bit, upsample_factor)
    e_upsampled = np.repeat(e_resampled_8bit, upsample_factor)
    i_upsampled = np.repeat(i_resampled_8bit, upsample_factor)

    # Modulate each signal
    t = np.arange(len(a_upsampled)) / fs_multiplexed
    modulated_a = a_upsampled * np.cos(2 * np.pi * fc1 * t)
    modulated_e = e_upsampled * np.cos(2 * np.pi * fc2 * t)
    modulated_i = i_upsampled * np.cos(2 * np.pi * fc3 * t)

    # Sum the modulated signals to create the multiplexed signal
    multiplexed = modulated_a + modulated_e + modulated_i

    # 6. Plot spectrum of multiplexed signal
    plot_spectrum(multiplexed, fs_multiplexed, 'Espectro de la señal multiplexada')

    # 7. Implement demultiplexing
    # Demodulate each channel
    demod_a = multiplexed * np.cos(2 * np.pi * fc1 * t)
    demod_e = multiplexed * np.cos(2 * np.pi * fc2 * t)
    demod_i = multiplexed * np.cos(2 * np.pi * fc3 * t)

    # Apply low-pass filter to recover the original signals
    demux_a = improved_bandpass_filter(demod_a, lowcut, highcut, fs_multiplexed)
    demux_e = improved_bandpass_filter(demod_e, lowcut, highcut, fs_multiplexed)
    demux_i = improved_bandpass_filter(demod_i, lowcut, highcut, fs_multiplexed)

    # Downsample back to 8 kHz
    demux_a = signal.resample_poly(demux_a, 1, upsample_factor)
    demux_e = signal.resample_poly(demux_e, 1, upsample_factor)
    demux_i = signal.resample_poly(demux_i, 1, upsample_factor)

    # 8. Plot spectra of demultiplexed signals
    plot_spectrum(demux_a, fs_new, 'Espectro de la señal demultiplexada "a"')
    plot_spectrum(demux_e, fs_new, 'Espectro de la señal demultiplexada "e"')
    plot_spectrum(demux_i, fs_new, 'Espectro de la señal demultiplexada "i"')

    processed_a = demux_a
    processed_e = demux_e
    processed_i = demux_i

def load_or_record_signals():
    global a_signal, e_signal, i_signal
    a_signal = check_or_record_audio('a.wav')
    e_signal = check_or_record_audio('e.wav')
    i_signal = check_or_record_audio('i.wav')
    messagebox.showinfo("Carga/Grabación", "Señales cargadas o grabadas correctamente")

def play_original_a():
    global a_signal
    if a_signal is not None:
        sd.play(a_signal, fs)
        sd.wait()
    else:
        messagebox.showerror("Error", "No hay señal original para 'a'")

def play_original_e():
    global e_signal
    if e_signal is not None:
        sd.play(e_signal, fs)
        sd.wait()
    else:
        messagebox.showerror("Error", "No hay señal original para 'e'")

def play_original_i():
    global i_signal
    if i_signal is not None:
        sd.play(i_signal, fs)
        sd.wait()
    else:
        messagebox.showerror("Error", "No hay señal original para 'i'")

def play_processed_a():
    global processed_a
    if processed_a is not None:
        sd.play(processed_a, 8000)
        sd.wait()
    else:
        messagebox.showerror("Error", "No hay señal procesada para 'a'")

def play_processed_e():
    global processed_e
    if processed_e is not None:
        sd.play(processed_e, 8000)
        sd.wait()
    else:
        messagebox.showerror("Error", "No hay señal procesada para 'e'")

def play_processed_i():
    global processed_i
    if processed_i is not None:
        sd.play(processed_i, 8000)
        sd.wait()
    else:
        messagebox.showerror("Error", "No hay señal procesada para 'i'")

class AudioPlayerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Audio Signal Processor")
        
        self.create_widgets()
        
    def create_widgets(self):
        self.load_button = ttk.Button(self.master, text="Load/Record Signals", command=load_or_record_signals)
        self.load_button.pack(pady=5)
        
        self.process_button = ttk.Button(self.master, text="Process Signals", command=process_signals)
        self.process_button.pack(pady=5)
        
        self.create_audio_controls("Original A", play_original_a)
        self.create_audio_controls("Original E", play_original_e)
        self.create_audio_controls("Original I", play_original_i)
        self.create_audio_controls("Processed A", play_processed_a)
        self.create_audio_controls("Processed E", play_processed_e)
        self.create_audio_controls("Processed I", play_processed_i)
        
    def create_audio_controls(self, label, play_command):
        frame = ttk.Frame(self.master)
        frame.pack(pady=5)
        
        ttk.Label(frame, text=label).pack(side=tk.LEFT)
        ttk.Button(frame, text="Play", command=play_command).pack(side=tk.LEFT)
        ttk.Button(frame, text="Stop", command=self.stop_audio).pack(side=tk.LEFT)
    
    def stop_audio(self):
        sd.stop()

# Inicializar las señales globales
a_signal = None
e_signal = None
i_signal = None
processed_a = None
processed_e = None
processed_i = None

# Crear la GUI
root = tk.Tk()
app = AudioPlayerGUI(root)
root.mainloop()
