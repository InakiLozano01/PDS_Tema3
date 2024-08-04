import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write, read
from scipy import signal as sig
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, ttk
import os
import threading
import time

# Parámetros de grabación
fs = 24000  # Frecuencia de muestreo de 24 KHz (múltiplo de 8 KHz)

# Función para grabar una señal de audio con ventana de control
def check_or_record_audio(filename):
    if os.path.exists(filename):
        print(f"Archivo {filename} encontrado. Cargando...")
        sample_rate, audio = read(filename)
        if sample_rate != fs:
            print(f"Advertencia: La frecuencia de muestreo del archivo {filename} es {sample_rate} Hz, no {fs} Hz como se esperaba.")
        return audio
    else:
        # Ventana de control para la grabación
        record_window = tk.Toplevel(root)
        record_window.title("Control de Grabación")

        def start_recording():
            duration = float(duration_entry.get())
            print(f"Grabando {filename} por {duration} segundos...")
            audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')

            def update_progress():
                elapsed_time = 0
                while elapsed_time < duration:
                    elapsed_time += 0.1
                    progress_var.set(elapsed_time / duration * 100)
                    record_window.update_idletasks()
                    time.sleep(0.1)
                sd.wait()
                write(filename, fs, audio)
                record_window.destroy()

            threading.Thread(target=update_progress).start()
            return audio

        ttk.Label(record_window, text="Duración de grabación (s):").pack(pady=5)
        duration_entry = ttk.Entry(record_window)
        duration_entry.pack(pady=5)
        duration_entry.insert(0, "10")

        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(record_window, variable=progress_var, maximum=100)
        progress_bar.pack(pady=5, fill=tk.X, padx=10)

        ttk.Button(record_window, text="Comenzar grabación", command=start_recording).pack(pady=5)

        root.wait_window(record_window)
        return check_or_record_audio(filename)

def improved_bandpass_filter(data, lowcut, highcut, fs, order=10):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = sig.butter(order, [low, high], btype='band', analog=False, output='sos')
    filtered_data = sig.sosfilt(sos, data)
    return filtered_data

def lowpass_filter(data, cutoff, fs, order=6):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    sos = sig.butter(order, normal_cutoff, btype='low', analog=False, output='sos')
    filtered_data = sig.sosfilt(sos, data)
    return filtered_data

def plot_spectrum_and_time(signal, fs, title):
    n = len(signal)
    t = np.arange(n) / fs
    k = np.arange(n)
    T = n / fs
    frq = k / T
    frq = frq[range(n//2)]
    Y = np.fft.fft(signal) / n
    Y = Y[range(n//2)]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    ax1.plot(t, signal)
    ax1.set_title(f'{title} - Time Domain')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amplitude')
    
    ax2.plot(frq, abs(Y))
    ax2.set_title(f'{title} - Frequency Domain')
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Amplitude')
    
    plt.tight_layout()
    plt.show()

def modulate(signal, fc, fs):
    t = np.arange(len(signal)) / fs
    window = sig.windows.hann(len(t))
    return signal * np.cos(2 * np.pi * fc * t) * window

def demodulate(signal, fc, fs):
    t = np.arange(len(signal)) / fs
    window = sig.windows.hann(len(t))
    demodulated = signal * np.cos(2 * np.pi * fc * t) * window
    return improved_bandpass_filter(demodulated, 300, 3400, fs)

def improved_spectral_subtraction(signal, noise_estimate, factor=1.0):
    if len(noise_estimate) < len(signal):
        noise_estimate = np.tile(noise_estimate, int(np.ceil(len(signal)/len(noise_estimate))))
    noise_estimate = noise_estimate[:len(signal)]
    
    signal_fft = np.fft.fft(signal)
    noise_fft = np.fft.fft(noise_estimate)
    
    signal_power = np.abs(signal_fft) ** 2
    noise_power = np.abs(noise_fft) ** 2
    
    clean_power = np.maximum(signal_power - factor * noise_power, 0)
    
    clean_mag = np.sqrt(clean_power)
    clean_phase = np.angle(signal_fft)
    clean_fft = clean_mag * np.exp(1j * clean_phase)
    clean_signal = np.fft.ifft(clean_fft).real
    
    return clean_signal

def notch_filter(data, fs, f0, Q=30.0):
    nyq = 0.5 * fs
    f0 = f0 / nyq
    b, a = sig.iirnotch(f0, Q)
    filtered_data = sig.filtfilt(b, a, data)
    return filtered_data

def process_signals():
    global a_signal, e_signal, i_signal, processed_a, processed_e, processed_i

    if a_signal is None or e_signal is None or i_signal is None:
        messagebox.showerror("Error", "Debe grabar todas las señales primero.")
        return

    lowcut = 300.0
    highcut = 3400.0
    a_filtered = improved_bandpass_filter(a_signal, lowcut, highcut, fs)
    e_filtered = improved_bandpass_filter(e_signal, lowcut, highcut, fs)
    i_filtered = improved_bandpass_filter(i_signal, lowcut, highcut, fs)

    # Apply notch filter to remove noise in the 3 kHz - 4 kHz range
    a_filtered = notch_filter(a_filtered, fs, f0=2800, Q=30.0)
    e_filtered = notch_filter(e_filtered, fs, f0=2800, Q=30.0)
    i_filtered = notch_filter(i_filtered, fs, f0=2800, Q=30.0)

    fs_new = 8000
    decimation_factor = int(fs / fs_new)
    
    nyq = 0.5 * fs
    cutoff = fs_new / 2
    N, beta = sig.kaiserord(60, width=(fs_new/2)/nyq)
    taps = sig.firwin(N, cutoff, window=('kaiser', beta), scale=True, nyq=nyq)

    a_resampled = sig.resample_poly(a_filtered, 1, decimation_factor, window=taps)
    e_resampled = sig.resample_poly(e_filtered, 1, decimation_factor, window=taps)
    i_resampled = sig.resample_poly(i_filtered, 1, decimation_factor, window=taps)

    a_resampled_8bit = np.int8(a_resampled / np.max(np.abs(a_resampled)) * 127)
    e_resampled_8bit = np.int8(e_resampled / np.max(np.abs(e_resampled)) * 127)
    i_resampled_8bit = np.int8(i_resampled / np.max(np.abs(i_resampled)) * 127)

    plot_spectrum_and_time(a_signal, fs, 'Señal original "a"')
    plot_spectrum_and_time(a_resampled_8bit, fs_new, 'Señal acondicionada "a"')
    plot_spectrum_and_time(e_signal, fs, 'Señal original "e"')
    plot_spectrum_and_time(e_resampled_8bit, fs_new, 'Señal acondicionada "e"')
    plot_spectrum_and_time(i_signal, fs, 'Señal original "i"')
    plot_spectrum_and_time(i_resampled_8bit, fs_new, 'Señal acondicionada "i"')

    fc1, fc2, fc3 = 62000, 66000, 70000

    fs_multiplexed = 192000
    upsample_factor = fs_multiplexed // fs_new
    
    a_upsampled = np.repeat(a_resampled_8bit, upsample_factor)
    e_upsampled = np.repeat(e_resampled_8bit, upsample_factor)
    i_upsampled = np.repeat(i_resampled_8bit, upsample_factor)

    modulated_a = modulate(a_upsampled, fc1, fs_multiplexed)
    modulated_e = modulate(e_upsampled, fc2, fs_multiplexed)
    modulated_i = modulate(i_upsampled, fc3, fs_multiplexed)

    multiplexed = modulated_a + modulated_e + modulated_i

    plot_spectrum_and_time(multiplexed, fs_multiplexed, 'Señal multiplexada')

    demod_a = demodulate(multiplexed, fc1, fs_multiplexed)
    demod_e = demodulate(multiplexed, fc2, fs_multiplexed)
    demod_i = demodulate(multiplexed, fc3, fs_multiplexed)

    #TODO: entender
    nyq = 0.5 * fs_multiplexed
    cutoff = fs_new / 2
    N, beta = sig.kaiserord(60, width=(fs_new/2)/nyq)
    taps = sig.firwin(N, cutoff, window=('kaiser', beta), scale=True, nyq=nyq)

    demux_a = sig.resample_poly(demod_a, 1, upsample_factor, window=taps)
    demux_e = sig.resample_poly(demod_e, 1, upsample_factor, window=taps)
    demux_i = sig.resample_poly(demod_i, 1, upsample_factor, window=taps)

    demux_a = improved_bandpass_filter(demux_a, lowcut, highcut, fs)
    demux_e = improved_bandpass_filter(demux_e, lowcut, highcut, fs)
    demux_i = improved_bandpass_filter(demux_i, lowcut, highcut, fs)


    #TODO: entender
    # Dynamic noise estimation specific for each signal
    noise_estimate_a = dynamic_noise_estimate(demux_a)
    noise_estimate_e = dynamic_noise_estimate(demux_e)
    noise_estimate_i = dynamic_noise_estimate(demux_i)
    
    demux_a = improved_spectral_subtraction(demux_a, noise_estimate_a)
    demux_e = improved_spectral_subtraction(demux_e, noise_estimate_e)
    demux_i = improved_spectral_subtraction(demux_i, noise_estimate_i)

    plot_spectrum_and_time(demux_a, fs_new, 'Señal demultiplexada "a"')
    plot_spectrum_and_time(demux_e, fs_new, 'Señal demultiplexada "e"')
    plot_spectrum_and_time(demux_i, fs_new, 'Señal demultiplexada "i"')

    processed_a = demux_a
    processed_e = demux_e
    processed_i = demux_i

def dynamic_noise_estimate(signal, threshold=0.02):
    silent_segments = signal[np.abs(signal) < threshold]
    return silent_segments

def load_or_record_signals():
    global a_signal, e_signal, i_signal
    a_signal = check_or_record_audio('a.wav')
    e_signal = check_or_record_audio('e.wav')
    i_signal = check_or_record_audio('i.wav')
    messagebox.showinfo("Carga/Grabación", "Señales cargadas o grabadas correctamente")

def play_audio(signal, fs):
    sd.play(signal, fs)
    sd.wait()

def play_original_a():
    global a_signal
    if a_signal is not None:
        threading.Thread(target=play_audio, args=(a_signal, fs)).start()
    else:
        messagebox.showerror("Error", "No hay señal original para 'a'")

def play_original_e():
    global e_signal
    if e_signal is not None:
        threading.Thread(target=play_audio, args=(e_signal, fs)).start()
    else:
        messagebox.showerror("Error", "No hay señal original para 'e'")

def play_original_i():
    global i_signal
    if i_signal is not None:
        threading.Thread(target=play_audio, args=(i_signal, fs)).start()
    else:
        messagebox.showerror("Error", "No hay señal original para 'i'")

def play_processed_a():
    global processed_a
    if processed_a is not None:
        threading.Thread(target=play_audio, args=(processed_a, 8000)).start()
    else:
        messagebox.showerror("Error", "No hay señal procesada para 'a'")

def play_processed_e():
    global processed_e
    if processed_e is not None:
        threading.Thread(target=play_audio, args=(processed_e, 8000)).start()
    else:
        messagebox.showerror("Error", "No hay señal procesada para 'e'")

def play_processed_i():
    global processed_i
    if processed_i is not None:
        threading.Thread(target=play_audio, args=(processed_i, 8000)).start()
    else:
        messagebox.showerror("Error", "No hay señal procesada para 'i'")

class AudioPlayerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Audio Signal Processor")
        
        self.create_widgets()
        
    def create_widgets(self):
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")
        self.style.configure("TLabel", padding=6)
        self.style.configure("TFrame", padding=6, background="#eee")

        frame = ttk.Frame(self.master, style="TFrame")
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.load_button = ttk.Button(frame, text="Load/Record Signals", command=load_or_record_signals, style="TButton")
        self.load_button.pack(pady=5)

        self.process_button = ttk.Button(frame, text="Process Signals", command=process_signals, style="TButton")
        self.process_button.pack(pady=5)

        self.create_audio_controls(frame, "Original A", play_original_a)
        self.create_audio_controls(frame, "Original E", play_original_e)
        self.create_audio_controls(frame, "Original I", play_original_i)
        self.create_audio_controls(frame, "Processed A", play_processed_a)
        self.create_audio_controls(frame, "Processed E", play_processed_e)
        self.create_audio_controls(frame, "Processed I", play_processed_i)
        
    def create_audio_controls(self, parent, label, play_command):
        frame = ttk.Frame(parent, style="TFrame")
        frame.pack(pady=5, fill=tk.X)

        ttk.Label(frame, text=label, style="TLabel").pack(side=tk.LEFT)
        ttk.Button(frame, text="Play", command=play_command, style="TButton").pack(side=tk.LEFT)
        ttk.Button(frame, text="Stop", command=self.stop_audio, style="TButton").pack(side=tk.LEFT)
    
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
