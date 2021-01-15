import os
from time import strftime, gmtime

import matplotlib.pyplot as plt

from scipy.signal import butter, lfilter

from main.constants import ARTIFACTS_DIR
from main.rr_extraction.qrs_detector.QRSDetectorOffline import QRSDetectorOffline


class ECGQRSDetectorOffline(QRSDetectorOffline):
    """
    Reasons for inheritance:
    1. QRSDetectorOffline class performs detection at the moment of creation
    2. QRSDetectorOffline class does not expect other value of signal frequency
    3. QRSDetectorOffline class works with the series coming from .csv file
    4. QRSDetectorOffline class has too greedy filter in `bandpass_filter` by default.
       Changed from `band` to `highpass`
    """

    def __init__(self, np_series, frequency):
        # 1. set the series for the overridden method `load_ecg_data` that directly sets `ecg_data_raw`
        # instead of reading from csv file
        self.np_series = np_series
        # 2. call the parent constructor, skipping its immediate detection
        super().__init__(None, verbose=False)
        # 3. set proper frequency coming from EDF files
        self.signal_frequency = frequency

    def load_ecg_data(self):
        self.ecg_data_raw = self.np_series

    def run(self, plot_data=False):
        self.detect_peaks()
        self.detect_qrs()
        if plot_data:
            os.makedirs(ARTIFACTS_DIR, exist_ok=True)
            self.plot_path = "{:s}/QRS_offline_detector_plot_{:s}.png".format(ARTIFACTS_DIR,
                                                                              strftime("%Y_%m_%d_%H_%M_%S",
                                                                                       gmtime()))
            self.plot_detection_data(show_plot=False)

    def bandpass_filter(self, data, lowcut, highcut, signal_freq, filter_order):
        """
        Method responsible for creating and applying Butterworth filter.
        :param deque data: raw data
        :param float lowcut: filter lowcut frequency value
        :param float highcut: filter highcut frequency value
        :param int signal_freq: signal frequency in samples per second (Hz)
        :param int filter_order: filter order
        :return array: filtered data
        """
        nyquist_freq = 0.5 * signal_freq
        low = lowcut / nyquist_freq
        high = highcut / nyquist_freq
        b, a = butter(filter_order, [high], btype="highpass")
        y = lfilter(b, a, data)
        return y

    def plot_detection_data(self, show_plot=False, from_idx=0, to_idx=None):
        """
        Method responsible for plotting detection results.
        :param bool show_plot: flag for plotting the results and showing plot
        """

        def plot_data(axis, data, title='', fontsize=10):
            axis.set_title(title, fontsize=fontsize)
            axis.grid(which='both', axis='both', linestyle='--')
            axis.plot(data, color="salmon", zorder=1)

        def plot_points(axis, values, indices):
            axis.scatter(x=indices, y=values[indices], c="black", s=50, zorder=2)

        plt.close('all')
        fig, axarr = plt.subplots(6, sharex=True, figsize=(15, 18))

        to_idx = to_idx or len(self.filtered_ecg_measurements)
        indices = [i - from_idx for i in self.qrs_peaks_indices if from_idx <= i <= to_idx]

        plot_data(axis=axarr[0], data=self.ecg_data_raw[from_idx:to_idx, 1], title='Raw ECG measurements')
        plot_data(axis=axarr[1], data=self.filtered_ecg_measurements[from_idx:to_idx],
                  title='Filtered ECG measurements')
        plot_data(axis=axarr[2], data=self.differentiated_ecg_measurements[from_idx:to_idx],
                  title='Differentiated ECG measurements')
        plot_data(axis=axarr[3], data=self.squared_ecg_measurements[from_idx:to_idx], title='Squared ECG measurements')
        plot_data(axis=axarr[4], data=self.integrated_ecg_measurements[from_idx:to_idx],
                  title='Integrated ECG measurements with QRS peaks marked (black)')
        plot_points(axis=axarr[4], values=self.integrated_ecg_measurements[from_idx:to_idx], indices=indices)
        plot_data(axis=axarr[5], data=self.ecg_data_detected[from_idx:to_idx, 1],
                  title='Raw ECG measurements with QRS peaks marked (black)')
        plot_points(axis=axarr[5], values=self.ecg_data_detected[:, 1], indices=indices)

        plt.tight_layout()
        fig.savefig(self.plot_path)

        if show_plot:
            plt.show()

        plt.close()
