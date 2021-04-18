import os
import re
from datetime import datetime

import pandas as pd


class StageMapping:
    def __init__(self, df_path, rat_id, experiment_date):
        df = pd.read_excel(df_path)
        self._df = df[(df['Rat ID'] == rat_id) & (df['Experiment Date'] == experiment_date)]
        if len(self._df) == 0:
            raise ValueError(f'Unable to find information for rat {rat_id} from {experiment_date}')
        self.experiment_number = self._df['Experiment ID'].values[0]
        self.learning_stage_id = self._df['Learning stage ID'].values[0]
        self.learning_stage_description = self._df['Learning stage description'].values[0].strip()


class SingleEntry:
    def __init__(self, rat_id, experiment_day, file_path):
        self.rat_id = rat_id
        self.experiment_day = experiment_day
        self.file_path: str = file_path


def walk_through_collected_raw_data(root_path):
    raw_meta_dataset = []
    dirpath, dirnames, _ = next(os.walk(root_path))
    for rat_id in dirnames:
        _, rat_experiment_days, _ = next(os.walk(os.path.join(root_path, rat_id)))
        rat_experiment_days = sorted(rat_experiment_days, key=lambda day: datetime.strptime(day, '%Y.%m.%d'))
        for experiment_number, experiment_day in enumerate(rat_experiment_days):
            current_path: str
            current_path, _, experiment_logs = next(os.walk(os.path.join(root_path, rat_id, experiment_day)))
            experiment_logs = sorted(experiment_logs,
                                     key=(lambda name:
                                          int(re.search(r'( - )(?P<duration>\d+)', name).group('duration'))
                                          ),
                                     reverse=True)
            file_to_extract: str
            for file_to_extract in experiment_logs:
                if not file_to_extract.endswith('.edf'):
                    continue
                raw_meta_dataset.append(SingleEntry(rat_id,
                                                    experiment_day,
                                                    os.path.join(current_path, file_to_extract)))
    return raw_meta_dataset
