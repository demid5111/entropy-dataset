import os

import pandas as pd

import sys
from main.constants import DATA_DIR, ROOT_DIR, ARTIFACTS_DIR
sys.path.insert(0, f'{ROOT_DIR}/main/entropier')

from main.dataset.generation.descriptors import ActionDescriptor, ECGDescriptor, ActionCode
from main.dataset.generation.single_behavior_act import SingleBehaviorAct
from main.rr_extraction.extractor import extract_rr_peaks
from main.dataset.generation.annotated_edf_signal import AnnotatedEDFSignal


class NoMoreActionsException(Exception):
    pass


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
    if start == -1 or stop == -1:
        raise NoMoreActionsException
    return ActionDescriptor(start, stop, action_type)


def extract_all_acts_from_single_file(rat_id, experiment_number, file_path):
    all_acts = []
    annotated_edf_signal = AnnotatedEDFSignal.from_edf_file(file_path)
    ecg_descriptor = ECGDescriptor(*extract_rr_peaks(annotated_edf_signal.ecg))
    date = annotated_edf_signal.eeg_ad_1._date_record
    data = annotated_edf_signal.behavior_class._data

    index_to_start = 0
    while True:
        try:
            action_descriptor = get_next_action(data, index_to_start=index_to_start)
            index_to_start = action_descriptor.stop_index + 1
        except NoMoreActionsException:
            break
        act = SingleBehaviorAct(action_descriptor=action_descriptor,
                                ecg_descriptor=ecg_descriptor,
                                rat_id=rat_id,
                                experiment_number=experiment_number,
                                experiment_date=date,
                                edf_signal=annotated_edf_signal,
                                source_file=file_path)
        print(action_descriptor)
        all_acts.append(act)
    return pd.DataFrame([act.to_dict() for act in all_acts])


if __name__ == '__main__':
    rat_id = 'T5'
    experiment_date = '2019.02.05'
    # TODO: fill the number
    EXPERIMENT_NUMBER = 1000

    file_name = os.path.join(DATA_DIR, rat_id, experiment_date, 'SN-00000042 - Track 2 - 1642 sec.edf')

    dataset_df = extract_all_acts_from_single_file(rat_id=rat_id,
                                                   experiment_number=EXPERIMENT_NUMBER,
                                                   file_path=file_name)

    dataset_path = os.path.join(ARTIFACTS_DIR, 'dataset.xlsx')
    dataset_df.index = dataset_df.index + 1
    dataset_df.to_excel(dataset_path)
    print(len(dataset_df))
