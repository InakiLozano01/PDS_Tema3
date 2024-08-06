import os
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd
from scipy.io.wavfile import read, write

# Función para grabar una señal de audio con ventana de control
def check_or_record_audio(filename, root, fs):
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
    
def load_or_record_signals(root, fs):
    global a_signal, e_signal, i_signal
    a_signal = check_or_record_audio('./audios/a.wav', root, fs)
    e_signal = check_or_record_audio('./audios/e.wav', root, fs)
    i_signal = check_or_record_audio('./audios/i.wav', root, fs)
    messagebox.showinfo("Carga/Grabación", "Señales cargadas o grabadas correctamente")
    return a_signal, e_signal, i_signal