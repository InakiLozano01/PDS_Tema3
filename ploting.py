import numpy as np
import matplotlib.pyplot as plt


def plot_spectrum_and_time(signal, fs, title, save=False, filename=None):
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
    
    if save and filename:
        plt.savefig(filename)
    else:
        plt.show()

def plot_signals(signals, fs, fs_multiplexed):

    plot_spectrum_and_time(signals.get("Original A"), fs, 'Señal original "a"')
    plot_spectrum_and_time(signals["Conditioned A"], 8000, 'Señal acondicionada "a"')
    plot_spectrum_and_time(signals["Original E"], fs, 'Señal original "e"')
    plot_spectrum_and_time(signals["Conditioned E"], 8000, 'Señal acondicionada "e"')
    plot_spectrum_and_time(signals["Original I"], fs, 'Señal original "i"')
    plot_spectrum_and_time(signals["Conditioned I"], 8000, 'Señal acondicionada "i"')
    plot_spectrum_and_time(signals["Multiplexed"], fs_multiplexed, 'Señal multiplexada')
    plot_spectrum_and_time(signals["Processed A"], 8000, 'Señal demultiplexada "a"')
    plot_spectrum_and_time(signals["Processed E"], 8000, 'Señal demultiplexada "e"')
    plot_spectrum_and_time(signals["Processed I"], 8000, 'Señal demultiplexada "i"')

def save_plots(signals, fs, fs_multiplexed):

    plot_spectrum_and_time(signals.get("Original A"), fs, 'Señal original "a"', save=True, filename='./images/original_a.png')
    plot_spectrum_and_time(signals["Conditioned A"], 8000, 'Señal acondicionada "a"', save=True, filename='./images/processed_a.png')
    plot_spectrum_and_time(signals["Original E"], fs, 'Señal original "e"', save=True, filename='./images/original_e.png')
    plot_spectrum_and_time(signals["Conditioned E"], 8000, 'Señal acondicionada "e"', save=True, filename='./images/processed_e.png')
    plot_spectrum_and_time(signals["Original I"], fs, 'Señal original "i"', save=True, filename='./images/original_i.png')
    plot_spectrum_and_time(signals["Conditioned I"], 8000, 'Señal acondicionada "i"', save=True, filename='./images/processed_i.png')
    plot_spectrum_and_time(signals["Multiplexed"], fs_multiplexed, 'Señal multiplexada', save=True, filename='./images/multiplexed.png')
    plot_spectrum_and_time(signals["Processed A"], 8000, 'Señal demultiplexada "a"', save=True, filename='./images/demux_a.png')
    plot_spectrum_and_time(signals["Processed E"], 8000, 'Señal demultiplexada "e"', save=True, filename='./images/demux_e.png')
    plot_spectrum_and_time(signals["Processed I"], 8000, 'Señal demultiplexada "i"', save=True, filename='./images/demux_i.png')