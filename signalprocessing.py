import numpy as np
import scipy.signal as sig
from tkinter import messagebox
from filters import improved_bandpass_filter


def modulate(signal, fc, fs):
    t = np.arange(len(signal)) / fs
    window = sig.windows.hann(len(t))
    return signal * np.cos(2 * np.pi * fc * t) * window

def demodulate(signal, fc, fs):
    t = np.arange(len(signal)) / fs
    window = sig.windows.hann(len(t))
    demodulated = signal * np.cos(2 * np.pi * fc * t) * window
    return improved_bandpass_filter(demodulated, 300, 3400, fs)

def process_signals(a_signal, e_signal, i_signal, fs):

    if a_signal is None or e_signal is None or i_signal is None:
        messagebox.showerror("Error", "Debe grabar todas las señales primero.")
        return

    lowcut = 300.0
    highcut = 3400.0
    a_filtered = improved_bandpass_filter(a_signal, lowcut, highcut, fs)
    e_filtered = improved_bandpass_filter(e_signal, lowcut, highcut, fs)
    i_filtered = improved_bandpass_filter(i_signal, lowcut, highcut, fs)

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

    processed_a = a_resampled_8bit
    processed_e = e_resampled_8bit
    processed_i = i_resampled_8bit

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

    demod_a = demodulate(multiplexed, fc1, fs_multiplexed)
    demod_e = demodulate(multiplexed, fc2, fs_multiplexed)
    demod_i = demodulate(multiplexed, fc3, fs_multiplexed)

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

    return processed_a, processed_e, processed_i, demux_a, demux_e, demux_i, fs_multiplexed, multiplexed