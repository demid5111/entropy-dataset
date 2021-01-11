import os
import io
from datetime import datetime

import numpy as np
import pandas as pd

from main.constants import DATA_DIR, ROOT_DIR, ARTIFACTS_DIR

import sys

from main.entropier.src.core.report import SampEnReport

sys.path.insert(0, f'{ROOT_DIR}/main/entropier')
print(sys.path)

from main.dataset.generation.annotated_edf_signal import AnnotatedEDFSignal
from main.entropier.src.core.sampen import SampEn
from main.entropier.src.utils.supporting import CalculationType


class ActionCode:
    """
    +1 - pedal event
    -1 - feeder event
    0 - no event
    """
    pedal = 1
    feeder = -1


class ActionDescriptor:
    start_index = None
    stop_index = None
    action: ActionCode = None

    def __init__(self, start_index, stop_index, action):
        self.start_index = start_index
        self.stop_index = stop_index
        self.action = action

    def __str__(self):
        mapping = {
            ActionCode.pedal: 'pedal',
            ActionCode.feeder: 'feeder'
        }
        return f'ActionDescriptor: ({self.start_index}, {self.stop_index}), action type: {mapping[self.action]}'


def get_next_action(data, index_to_start):
    action_type = None
    mapping = {
        1: ActionCode.pedal,
        -1: ActionCode.feeder
    }

    is_action_started = False
    start = -1
    stop = -1
    for i in range(index_to_start, len(data)):
        if data[i] != 0 and not is_action_started:
            is_action_started = True
            action_type = mapping[data[i]]
            start = i
        elif data[i] == 0 and is_action_started:
            stop = i
            break
    return ActionDescriptor(start, stop, action_type)


class SingleBehaviorAct:
    def __init__(self, desc: ActionDescriptor, rat_id: str, experiment_number: int, experiment_date: datetime,
                 edf_signal: AnnotatedEDFSignal,
                 source_file: str):
        # utility fields
        self._source_file: str = source_file
        self._edf_signal = edf_signal

        # TODO: need some material from Anastasya
        self.stage_learning = None

        # constructor parameters
        self.rat_id = rat_id
        self.experiment_number = experiment_number
        self.experiment_date = experiment_date

        # filled from descriptor
        self.behaviour_type = desc.action
        self.raw_time_start = desc.start_index
        self.raw_time_end = desc.stop_index

        # calculated attributes, empty by default, just numbers
        self.eeg_sampen_ad1: int = self.calculate_sampen(self.extract_my_AD(1))
        self.eeg_sampen_ad2: int = self.calculate_sampen(self.extract_my_AD(2))
        self.eeg_sampen_ad3: int = self.calculate_sampen(self.extract_my_AD(3))
        self.ecg_avg_rr: int = -1
        self.ecg_sdnn_rr: int = -1
        self.ecg_sampen_rr: int = -1
        self.ecg_permen_rr: int = -1
        self.ecg_n_rr: int = -1

    def extract_my_AD(self, ad_index):
        return self._edf_signal.__getattribute__(f'eeg_ad_{ad_index}')._data[self.raw_time_start: self.raw_time_end]

    def dump_tmp_series(self, series):
        tmp_df = pd.DataFrame(series)
        csv_line = tmp_df.to_csv(sep='\n', decimal='.', index=False)
        ignore_leading_zero = csv_line[2:] if csv_line.index('0\n') == 0 else csv_line

        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        new_path = os.path.join(ARTIFACTS_DIR, 'tmp.txt')
        with open(os.path.join(ARTIFACTS_DIR, 'tmp.txt'), 'w') as f:
            f.write(ignore_leading_zero)
        return new_path

    def calculate_sampen(self, series) -> int:
        # TODO: call entropier directly instead of intermediate file
        tmp_file_path = self.dump_tmp_series(series)

        # calculate for a whole series
        report: SampEnReport = SampEn().prepare_calculate_window_sampen(m=10,
                                                                        file_name=tmp_file_path,
                                                                        calculation_type=CalculationType.CONST,
                                                                        dev_coef_value=-.0,
                                                                        use_threshold=False,
                                                                        threshold_value=-.0)
        return report.result_values[0]


if __name__ == '__main__':
    rat_id = 'T5'
    experiment_date = '2019.02.05'
    # TODO: fill the number
    EXPERIMENT_NUMBER = 1000
    file_name = os.path.join(DATA_DIR, rat_id, experiment_date, 'SN-00000042 - Track 2 - 1642 sec.edf')
    annotated_edf_signal = AnnotatedEDFSignal.from_edf_file(file_name)
    print(annotated_edf_signal)

    action_descriptor = get_next_action(annotated_edf_signal.behavior_class._data, index_to_start=0)
    date = annotated_edf_signal.eeg_ad_1._date_record
    act = SingleBehaviorAct(desc=action_descriptor,
                            rat_id=rat_id, experiment_number=EXPERIMENT_NUMBER,
                            experiment_date=date,
                            edf_signal=annotated_edf_signal,
                            source_file=file_name)
    print(action_descriptor)
