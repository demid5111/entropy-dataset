import pyedflib

import matplotlib.pyplot as plt

import numpy as np


def read_ir_signal_from(edf_file_path):
    f = pyedflib.EdfReader(edf_file_path)
    signal_labels = f.getSignalLabels()
    ir_index = signal_labels.index('IR')

    ir_buffer = f.readSignal(ir_index)
    ir_frequency = f.getSampleFrequency(ir_index)
    date_record = f.getStartdatetime()
    return ir_buffer, ir_frequency, date_record


def visualize_signal(signal, left=None, right=None):
    np.random.seed(19680801)
    plt.subplot(211)
    plt.plot(signal)
    plt.subplot(212)
    left_border = left if left is not None else 0
    right_border = right + 1 if right is not None and right + 1 < len(signal) else len(signal)
    plt.plot(signal[left_border:right_border])
    plt.show()


def is_difference_meaningful(first_value, second_value, diff_threshold=0.1):
    max_value = max(first_value, second_value)
    min_value = min(first_value, second_value)
    return abs((max_value / min_value) - 1) > diff_threshold


def is_difference_negligible(first_value, second_value, diff_threshold=0.1):
    max_value = max(first_value, second_value)
    min_value = min(first_value, second_value)
    return abs((max_value / min_value) - 1) < diff_threshold
