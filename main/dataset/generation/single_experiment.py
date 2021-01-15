import pandas as pd

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
                                      file_path):
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
