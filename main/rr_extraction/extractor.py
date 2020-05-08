import numpy as np

from main.rr_extraction.ecg_qrs_detector import ECGQRSDetectorOffline
from main.rr_extraction.ecg_raw_signal import ECGRawSignal


def indices_to_intervals(indices, frequency):
    intervals = np.zeros((len(indices),))
    ms_times = (np.array(indices) / frequency) * 1000
    for i, time_value in enumerate(ms_times):
        prev_time = 0 if i == 0 else ms_times[i - 1]
        intervals[i] = time_value - prev_time
    return intervals, ms_times


def extract_rr_peaks(raw_signal: ECGRawSignal, plot_data=False):
    detector = ECGQRSDetectorOffline(raw_signal.indexed_series, raw_signal._ir_frequency)
    detector.run(plot_data=plot_data)
    intervals, ms_times = indices_to_intervals(detector.qrs_peaks_indices, raw_signal._ir_frequency)
    return intervals, ms_times
