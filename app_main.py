import sounddevice as sd
import numpy as np
from scipy import signal as sig
import tkinter as tk
from tkinter import ttk
import threading
import queue
from audiorecord import load_or_record_signals
from filters import improved_bandpass_filter
from signalprocessing import process_signals
from ploting import plot_signals, save_plots
from playaudio import *

# Parámetros de grabación
fs = 24000  # Frecuencia de muestreo de 24 KHz (múltiplo de 8 KHz)
real_time_processing = False

def start_real_time_processing():
    global real_time_processing
    real_time_processing = True
    
    audio_queue = queue.Queue() # Define the audio_queue
    record_thread = threading.Thread(target=record_audio, args=(audio_queue, fs))
    process_thread = threading.Thread(target=process_audio, args=(audio_queue, fs, 16000))
    
    record_thread.start()
    process_thread.start()

def stop_real_time_processing():
    global real_time_processing
    real_time_processing = False

# Función para grabar el audio
def record_audio(queue, fs):
    while real_time_processing:
        audio = sd.rec(int(1 * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        audio = audio.flatten()
        queue.put(audio)

def process_audio(queue, fs, new_fs):
    while real_time_processing:
        if not queue.empty():
            audio = queue.get()
            filtered_audio = improved_bandpass_filter(audio, 300, 3400, fs)
            
            # Resamplear el audio filtrado
            new_fs = 8000 # Nueva tasa de muestreo deseada
            filtered_audio_resampled = sig.resample_poly(filtered_audio, new_fs, fs)
            
            filtered_audio_8bit = np.int8(filtered_audio_resampled / np.max(np.abs(filtered_audio_resampled)) * 127)
            sd.play(filtered_audio_8bit, new_fs)
            sd.wait()

class AudioPlayerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Audio Signal Processor")
        
        self.create_widgets()

    def load_signals(self):
        global a_signal, e_signal, i_signal
        a_signal, e_signal, i_signal = load_or_record_signals(self.master, 24000)
    
    def signal_processing(self):
        global processed_a, processed_e, processed_i, demux_a, demux_e, demux_i, fs_multiplexed, multiplexed
        processed_a, processed_e, processed_i, demux_a, demux_e, demux_i, fs_multiplexed, multiplexed = process_signals(a_signal, e_signal, i_signal, 24000)
        
    def create_widgets(self):
        global a_signal, e_signal, i_signal, processed_a, processed_e, processed_i, demux_a, demux_e, demux_i, multiplexed, fs_multiplexed
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")
        self.style.configure("TLabel", padding=6)
        self.style.configure("TFrame", padding=6, background="#eee")

        frame = ttk.Frame(self.master, style="TFrame")
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.load_button = ttk.Button(frame, text="Load/Record Signals", command=self.load_signals, style="TButton")
        self.load_button.pack(pady=5)

        self.process_button = ttk.Button(frame, text="Process Signals", command=self.signal_processing, style="TButton")
        self.process_button.pack(pady=5)

        self.plot_button = ttk.Button(frame, text="Plot Signals", command=self.plot_signals_wrapper, style="TButton")
        self.plot_button.pack(pady=5)

        self.save_plots_button = ttk.Button(frame, text="Save Plots", command=self.save_plots_wrapper, style="TButton")
        self.save_plots_button.pack(pady=5)

        self.create_audio_controls(frame, "Original A", lambda: play_original_a(a_signal, 24000))
        self.create_audio_controls(frame, "Original E", lambda: play_original_e(e_signal, 24000))
        self.create_audio_controls(frame, "Original I", lambda: play_original_i(i_signal, 24000))
        self.create_audio_controls(frame, "Conditioned A", lambda: play_conditioned_a(processed_a))
        self.create_audio_controls(frame, "Conditioned E", lambda: play_conditioned_e(processed_e))
        self.create_audio_controls(frame, "Conditioned I", lambda: play_conditioned_i(processed_i))
        self.create_audio_controls(frame, "Processed A", lambda: play_processed_a(demux_a))
        self.create_audio_controls(frame, "Processed E", lambda: play_processed_e(demux_e))
        self.create_audio_controls(frame, "Processed I", lambda: play_processed_i(demux_i))
        
        self.real_time_button = ttk.Button(frame, text="Start Real-Time Processing", command=start_real_time_processing, style="TButton")
        self.real_time_button.pack(pady=5)
        
        self.stop_real_time_button = ttk.Button(frame, text="Stop Real-Time Processing", command=stop_real_time_processing, style="TButton")
        self.stop_real_time_button.pack(pady=5)

    def plot_signals_wrapper(self):
        global a_signal, e_signal, i_signal, processed_a, processed_e, processed_i, demux_a, demux_e, demux_i, multiplexed, fs_multiplexed
        signals = {
            "Original A": a_signal,
            "Original E": e_signal,
            "Original I": i_signal,
            "Conditioned A": processed_a,
            "Conditioned E": processed_e,
            "Conditioned I": processed_i,
            "Processed A": demux_a,
            "Processed E": demux_e,
            "Processed I": demux_i,
            "Multiplexed": multiplexed
        }
        plot_signals(signals, fs, fs_multiplexed)

    def save_plots_wrapper(self):
        global a_signal, e_signal, i_signal, processed_a, processed_e, processed_i, demux_a, demux_e, demux_i, multiplexed, fs_multiplexed
        signals = {
            "Original A": a_signal,
            "Original E": e_signal,
            "Original I": i_signal,
            "Conditioned A": processed_a,
            "Conditioned E": processed_e,
            "Conditioned I": processed_i,
            "Processed A": demux_a,
            "Processed E": demux_e,
            "Processed I": demux_i,
            "Multiplexed": multiplexed
        }
        save_plots(signals, fs, fs_multiplexed)

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
demux_a = None
demux_e = None
demux_i = None
multiplexed = None

# Crear la GUI
root = tk.Tk()
app = AudioPlayerGUI(root)
root.mainloop()
