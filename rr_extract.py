import os

from main.constants import DATA_DIR, DATA_ROOT_DIR
from main.rr_extraction.ecg_raw_signal import ECGRawSignal
from main.rr_extraction.extractor import extract_rr_peaks

if __name__ == '__main__':
    file_name = os.path.join(DATA_DIR, 'T5', '2019.02.05', 'SN-00000042 - Track 2 - 1642 sec.edf')
    ecg_raw_signal = ECGRawSignal.from_edf(file_name)

    file_name = os.path.join(DATA_ROOT_DIR, 'reference_ecg_humans', 'AH_1', 'SC5_1', 'ecg_AH_1_SC5_1.txt')
    frequency = 250
    ecg_txt_signal = ECGRawSignal.from_txt(file_name, frequency)
    intervals, ms_times = extract_rr_peaks(ecg_txt_signal)
