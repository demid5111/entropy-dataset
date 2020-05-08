import numpy as np
import pyedflib


def read_signal_from(edf_file_path, edf_label):
    signals, signal_headers, header = pyedflib.highlevel.read_edf(edf_file_path)
    ir_index = None
    for i, signal_header in enumerate(signal_headers):
        if signal_header['label'] == edf_label:
            ir_index = i

    ir_buffer = signals[ir_index]
    ir_frequency = signal_headers[ir_index]['sample_rate']
    date_record = header['startdate']
    return ir_buffer, ir_frequency, date_record


class RawSignal:
    edf_label = None

    def __init__(self, series, ir_frequency, date_record):
        self._data = series
        self._start_offset = 0
        self._ir_frequency = ir_frequency
        self._date_record = date_record
        self._min_value = np.amin(self._data)

    @classmethod
    def from_edf(cls, edf_file_path):
        ir_buffer, ir_frequency, date_record = read_signal_from(edf_file_path, cls.edf_label)
        return cls(ir_buffer, ir_frequency, date_record)

    @classmethod
    def from_labeled_signal(cls, labeled_signal, raw_series):
        return cls(raw_series, labeled_signal.raw_signal._ir_frequency, labeled_signal.raw_signal._date_record)
