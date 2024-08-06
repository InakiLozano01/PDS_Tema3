import sounddevice as sd
import threading
from tkinter import messagebox


def play_audio(signal, fs):
    sd.play(signal, fs)
    sd.wait()

def play_original_a(a_signal, fs):
    if a_signal is not None:
        threading.Thread(target=play_audio, args=(a_signal, fs)).start()
    else:
        messagebox.showerror("Error", "No hay señal original para 'a'")

def play_original_e(e_signal, fs):
    if e_signal is not None:
        threading.Thread(target=play_audio, args=(e_signal, fs)).start()
    else:
        messagebox.showerror("Error", "No hay señal original para 'e'")

def play_original_i(i_signal, fs):
    if i_signal is not None:
        threading.Thread(target=play_audio, args=(i_signal, fs)).start()
    else:
        messagebox.showerror("Error", "No hay señal original para 'i'")

def play_processed_a(demux_a):
    if demux_a is not None:
        threading.Thread(target=play_audio, args=(demux_a, 8000)).start()
    else:
        messagebox.showerror("Error", "No hay señal procesada para 'a'")

def play_processed_e(demux_e):
    if demux_e is not None:
        threading.Thread(target=play_audio, args=(demux_e, 8000)).start()
    else:
        messagebox.showerror("Error", "No hay señal procesada para 'e'")

def play_processed_i(demux_i):
    if demux_i is not None:
        threading.Thread(target=play_audio, args=(demux_i, 8000)).start()
    else:
        messagebox.showerror("Error", "No hay señal procesada para 'i'")

def play_conditioned_a(processed_a):
    if processed_a is not None:
        threading.Thread(target=play_audio, args=(processed_a, 8000)).start()
    else:
        messagebox.showerror("Error", "No hay señal acondicionada para 'a'")

def play_conditioned_e(processed_e):
    if processed_e is not None:
        threading.Thread(target=play_audio, args=(processed_e, 8000)).start()
    else:
        messagebox.showerror("Error", "No hay señal acondicionada para 'e'")

def play_conditioned_i(processed_i):
    if processed_i is not None:
        threading.Thread(target=play_audio, args=(processed_i, 8000)).start()
    else:
        messagebox.showerror("Error", "No hay señal acondicionada para 'i'")