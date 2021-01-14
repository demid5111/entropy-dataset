import os
from datetime import timedelta, datetime

import numpy as np
import pandas as pd

from main.constants import ARTIFACTS_DIR
from main.dataset.generation.descriptors import ActionDescriptor, ECGDescriptor, ActionCode
from main.dataset.generation.annotated_edf_signal import AnnotatedEDFSignal
from main.entropier.src.core.permen import PermutationEntropy
from main.entropier.src.core.report import SampEnReport, PermutationEntropyReport
from main.entropier.src.core.sampen import SampEn
from main.entropier.src.utils.supporting import CalculationType


class SingleBehaviorAct:
    def __init__(self,
                 action_descriptor: ActionDescriptor,
                 ecg_descriptor: ECGDescriptor,
                 rat_id: str,
                 experiment_number: int,
                 experiment_date: datetime,
                 learning_stage_id: int,
                 learning_stage_description: str,
                 edf_signal: AnnotatedEDFSignal,
                 source_file: str):
        # utility fields
        self._source_file: str = source_file
        self._edf_signal: AnnotatedEDFSignal = edf_signal
        self._ecg_descriptor = ecg_descriptor
        self._action_descriptor = action_descriptor

        # constructor parameters
        self.rat_id = rat_id
        self.experiment_number = experiment_number
        self.experiment_date = experiment_date
        self.learning_stage_id = learning_stage_id
        self.learning_stage_description = learning_stage_description

        # filled from descriptor
        self.behaviour_type = self._action_descriptor.action
        self.raw_time_start = self._action_descriptor.start_index
        self.raw_time_end = self._action_descriptor.stop_index

        # calculated attributes, empty by default, just numbers
        self.eeg_sampen_ad1: int = self.calculate_sampen(self.extract_my_eeg(1)).result_values[0]
        self.eeg_sampen_ad2: int = self.calculate_sampen(self.extract_my_eeg(2)).result_values[0]
        self.eeg_sampen_ad3: int = self.calculate_sampen(self.extract_my_eeg(3)).result_values[0]

        rr_intervals = self.extract_my_ecg()
        rr_sampen_report: SampEnReport = self.calculate_sampen(rr_intervals)
        self.ecg_avg_rr: int = getattr(rr_sampen_report, 'avg_rr_values', {0: 'N/A'})[0]
        self.ecg_sdnn_rr: int = np.std(rr_intervals)
        self.ecg_sampen_rr: int = getattr(rr_sampen_report, 'result_values', {0: 'N/A'})[0]
        self.ecg_permen_rr: int = getattr(self.calculate_permen(rr_intervals), 'result_values', {0: 'N/A'})[0]
        self.ecg_n_rr: int = len(rr_intervals)

    def extract_my_eeg(self, ad_index):
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

    def calculate_sampen(self, series) -> SampEnReport:
        # TODO: call entropier directly instead of intermediate file
        tmp_file_path = self.dump_tmp_series(series)

        # calculate for a whole series
        report: SampEnReport = SampEn().prepare_calculate_window_sampen(m=10,
                                                                        file_name=tmp_file_path,
                                                                        calculation_type=CalculationType.CONST,
                                                                        dev_coef_value=-.0,
                                                                        use_threshold=False,
                                                                        threshold_value=-.0)
        return report

    def calculate_permen(self, series) -> PermutationEntropyReport:
        # TODO: call entropier directly instead of intermediate file
        tmp_file_path = self.dump_tmp_series(series)

        # calculate for a whole series
        report: PermutationEntropyReport = PermutationEntropy().prepare_calculate_windowed(m=10,
                                                                        file_name=tmp_file_path,
                                                                        calculation_type=CalculationType.CONST,
                                                                        dev_coef_value=-.0,
                                                                        use_threshold=False,
                                                                        threshold_value=-.0)
        return report

    def extract_my_ecg(self):
        intervals = self._ecg_descriptor.intervals
        ms_times = self._ecg_descriptor.ms_times
        return intervals[np.logical_and(ms_times >= self.raw_time_start, ms_times <= self.raw_time_end)]

    def get_behavior(self):
        mapping = {
            ActionCode.pedal: 'pedal',
            ActionCode.feeder: 'feeder'
        }
        return mapping[self.behaviour_type]

    def to_dict(self):
        extract_delta = lambda x: (x // 100, (x/100)%(x//100) if x // 100 else 0)
        s, ms = extract_delta(self.raw_time_start)
        delta_start = timedelta(seconds=s, milliseconds=ms*1000)
        s, ms = extract_delta(self.raw_time_end)
        delta_end = timedelta(seconds=s, milliseconds=ms*1000)
        return {
            # constructor parameters
            '1. Learning Stage ID': self.learning_stage_id,
            '2. Learning Stage Description': self.learning_stage_description,
            '3. Rat ID': self.rat_id,
            '4. Number of Experiment': self.experiment_number,
            '5. Date of Experiment': self.experiment_date,

            # filled from descriptor
            '6. Behavior': self.get_behavior(),
            '7. Start time': self.experiment_date + delta_start,
            '8. Stop time': self.experiment_date + delta_end,

            # calculated attributes, empty by default, just numbers
            '9. EEG Sample Entropy (m=10, type=0.2*SD), channel: AD1': self.eeg_sampen_ad1,
            '10. EEG Sample Entropy (m=10, type=0.2*SD), channel: AD2': self.eeg_sampen_ad2,
            '11. EEG Sample Entropy (m=10, type=0.2*SD), channel: AD3': self.eeg_sampen_ad3,

            '12. ECG RR mean': self.ecg_avg_rr,
            '13. ECG RR SD':  self.ecg_sdnn_rr,
            '14. ECG RR count': self.ecg_n_rr,
            '15. ECG Sample Entropy (m=10, type=0.2*SD), channel: AD4': self.ecg_sampen_rr,
            '16. ECG Permutation Entropy (stride=1), channel: AD4':self.ecg_permen_rr,
        }
