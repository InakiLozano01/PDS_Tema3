import numpy as np
import scipy.signal as sig

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