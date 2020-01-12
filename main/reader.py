import pyedflib
import numpy as np
import os

from main.constants import DATA_DIR


if __name__ == '__main__':
    file_name = os.path.join(DATA_DIR, 'T7', '2019.02.21', 'SN-00000042 - Track 2 - 256 sec.edf')

    f = pyedflib.EdfReader(file_name)
    signal_number = f.signals_in_file
    signal_labels = f.getSignalLabels()

    sigbufs = np.zeros((signal_number, f.getNSamples()[0]))
    for i in np.arange(signal_number):
        signal = f.readSignal(i)
        print('Signal {}, shape: {}'.format(signal_labels[i], signal.shape))
        sigbufs[i, :signal.shape[0]] = signal
