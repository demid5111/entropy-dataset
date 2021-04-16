from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io

from main.dataset.generation.annotated_edf_signal import AnnotatedEDFSignal
from main.dataset.generation.descriptors import ECGDescriptor, ActionDescriptor, ActionCode
from main.dataset.generation.single_behavior_act import SingleBehaviorAct
from main.rr_extraction.extractor import extract_rr_peaks


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


def extract_all_acts_from_single_file(rat_id, experiment_number, learning_stage_id, learning_stage_description,
                                      file_path, use_enhanced_ecg_mat=True):
    """
    In original files ECG is quite noisy resulting in extremely poor RR intervals detection.
    In order to overcome this problem, each .edf file was imported to the Spike application
    and ECG signal was enhanced using the Spike internal methods.
    As a result, each .edf file in the dataset has the matching .smr and .s2r files
    .smr file is the official Spike file format, .s2r is the Spike additional file

    Spike .smr files have a well known format that we can read with third-party modules such as neo.
    However, due to the Spike design, an .smr file contains the original signal only. All signal modifications
    and derivatives are placed in .s2r files that are not well described, there are no available
    specifications or existing readers. So the only option to get the enhanced ECG signal is to
    export it explicitly to some known format and then read it.

    Therefore, the enhanced signal was exported as .mat files that are placed near each .edf file.
    When generating the dataset, we first read the .edf file and then replace the ECG signal with data from
    .mat files.

    Parameters
    ----------
    rat_id
    experiment_number
    learning_stage_id
    learning_stage_description
    file_path
    use_enhanced_ecg_mat

    Returns
    -------

    """
    all_acts = []
    annotated_edf_signal = AnnotatedEDFSignal.from_edf_file(file_path)
    if use_enhanced_ecg_mat:
        current_folder = Path(file_path).parent
        mat_path = current_folder / f'{Path(file_path).stem}.mat'
        if not mat_path.exists():
            print(f'ALARM No such file: {mat_path}')
        else:
            mat = scipy.io.loadmat(str(mat_path))

            appropriate_keys = [i for i in mat if not i.startswith('__')]
            if len(mat.keys()) > 4 or len(appropriate_keys) > 1:
                raise ValueError('Mat files with more than 1 channel are not supported')

            all_signals = mat[appropriate_keys[0]][0][0]
            if any(len(el) > 1 for i, el in enumerate(all_signals) if i < 8) or len(all_signals[8]) <= 1:
                raise ValueError('Mat files with such internal structure are not supported')

            ecg_signal = all_signals[8].flatten()  # reverse engineered index, check if you do no believe

            if len(ecg_signal) != len(annotated_edf_signal.ecg._data):
                raise ValueError('Original and new ECG signals do no match: '
                                 f'{len(annotated_edf_signal.ecg)} vs {len(ecg_signal)}')
            annotated_edf_signal.ecg.update_data(ecg_signal)
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
                                learning_stage_id=learning_stage_id,
                                learning_stage_description=learning_stage_description,
                                edf_signal=annotated_edf_signal,
                                source_file=file_path)
        all_acts.append(act)
    df = pd.DataFrame([act.to_dict() for act in all_acts])
    if not df.empty:
        df['5. Date of Experiment'] = df['5. Date of Experiment'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['7. Start time'] = df['7. Start time'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
        df['8. Stop time'] = df['8. Stop time'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    return df
