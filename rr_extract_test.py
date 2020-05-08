import os
import unittest

from main.constants import DATA_ROOT_DIR
from main.rr_extraction.ecg_raw_signal import ECGRawSignal, read_signal_from_txt
from main.rr_extraction.extractor import extract_rr_peaks


def compare_rr_times(expected, actual, delta):
    not_matched = []
    is_one_by_one_comparison_started = False
    expected_current_index = 0
    for i, actual_time_mark in enumerate(actual):
        diff = actual_time_mark - expected[expected_current_index]
        is_diff_negative = diff < 0
        is_diff_meaningful = diff > delta

        if is_diff_negative and not is_one_by_one_comparison_started:
            not_matched.append(actual_time_mark)
            is_one_by_one_comparison_started = True
            continue

        if i == 0:
            is_one_by_one_comparison_started = True

        if is_diff_meaningful and diff < 200:
            not_matched.append(actual_time_mark)

        if is_one_by_one_comparison_started and diff < 200:
            expected_current_index += 1

    return not_matched, len(not_matched) / max(len(actual), len(expected))


class RRExtractionHumanECGTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ir_frequency = 250
        self.humans_data_dir = os.path.join(DATA_ROOT_DIR, 'reference_ecg_humans')
        self.acceptable_delta = 33

    def compare_rr_intervals(self, ah_number, sc_numbers):
        ecg_path = os.path.join(self.humans_data_dir,
                                'AH_{}'.format(ah_number),
                                'SC{}_{}'.format(sc_numbers[0], sc_numbers[1]),
                                'ecg_AH_{0}_SC{1}_{2}.txt'.format(ah_number, sc_numbers[0], sc_numbers[1]))
        rr_path = ecg_path.replace('ecg_AH', 'rr_AH')
        seconds_times = read_signal_from_txt(rr_path)
        reference_ms_times = [int(i * 1000) for i in seconds_times]
        ecg_raw_signal = ECGRawSignal.from_txt(ecg_path, self.ir_frequency)
        intervals, ms_times = extract_rr_peaks(ecg_raw_signal)
        return compare_rr_times(expected=reference_ms_times, actual=ms_times, delta=self.acceptable_delta)

    def test_AH1_SC5_1(self):
        _, ratio = self.compare_rr_intervals(ah_number=1, sc_numbers=(5, 1))
        self.assertLessEqual(ratio, 0.0027)

    def test_AH1_SC5_2(self):
        _, ratio = self.compare_rr_intervals(ah_number=1, sc_numbers=(5, 2))
        self.assertLessEqual(ratio, 0.0096)

    def test_AH1_SC5_3(self):
        _, ratio = self.compare_rr_intervals(ah_number=1, sc_numbers=(5, 3))
        self.assertLessEqual(ratio, 0.00)

    def test_AH1_SC5_4(self):
        _, ratio = self.compare_rr_intervals(ah_number=1, sc_numbers=(5, 4))
        self.assertLessEqual(ratio, 0.00)

    def test_AH1_SC5_5(self):
        _, ratio = self.compare_rr_intervals(ah_number=1, sc_numbers=(5, 5))
        self.assertLessEqual(ratio, 0.00)

    def test_AH1_SC5_6(self):
        _, ratio = self.compare_rr_intervals(ah_number=1, sc_numbers=(5, 6))
        self.assertLessEqual(ratio, 0.00)

    def test_AH2_SC6_1(self):
        _, ratio = self.compare_rr_intervals(ah_number=2, sc_numbers=(6, 1))
        self.assertLessEqual(ratio, 0.0044)

    def test_AH2_SC6_2(self):
        _, ratio = self.compare_rr_intervals(ah_number=2, sc_numbers=(6, 2))
        self.assertLessEqual(ratio, 0.00)
