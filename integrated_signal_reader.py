import os

from main.constants import DATA_DIR


if __name__ == '__main__':
    file_name = os.path.join(DATA_DIR, 'T5', '2019.02.11', 'SN-00000042 - Track 1 - 2002 sec.edf')

    labeled_signal = IntegratedSignal.from_edf(file_name)
