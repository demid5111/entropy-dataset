from datetime import datetime

import numpy as np
import pandas as pd

from main.models.raw_signal import RawSignal


def read_signal_from_txt(path):
    df = pd.read_table(path,
                       sep='\n',
                       dtype=np.float64,
                       decimal='.',
                       header=None)
    return df[0].to_numpy()


class ECGRawSignal(RawSignal):
    edf_label = 'AD4'

    @property
    def indexed_series(self):
        return np.array(list(enumerate(self._data)))

    @classmethod
    def from_txt(cls, edf_file_path, ir_frequency):
        date_record = datetime.now()
        ir_buffer = read_signal_from_txt(edf_file_path)
        return cls(ir_buffer, ir_frequency, date_record)
