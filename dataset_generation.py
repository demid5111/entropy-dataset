import os

from main.constants import DATA_DIR
from main.dataset.generation.annotated_edf_signal import AnnotatedEDFSignal

if __name__ == '__main__':
    file_name = os.path.join(DATA_DIR, 'T5', '2019.02.05', 'SN-00000042 - Track 2 - 1642 sec.edf')
    annotated_edf_signal = AnnotatedEDFSignal.from_edf_file(file_name)
    print(annotated_edf_signal)
