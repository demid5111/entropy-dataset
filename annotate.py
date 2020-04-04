import os

from main.annotation.activation import ActionsClassifier
from main.annotation.cleanup_signal import SingleEventsEliminator
from main.annotation.writer import EDFAnnotationChannelAppender
from main.constants import DATA_DIR
from main.signal.ir_raw_signal import IRRawSignal
from main.signal.labeled_signal import LabeledSignal


def list_all_files(root_dir):
    edf_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            name, ext = os.path.splitext(file)
            if ext == '.edf':
                edf_files.append(os.path.join(root, file))
    return edf_files


def annotate_single_file(target_file_name):
    labeled_signal = LabeledSignal.from_edf(target_file_name)
    SingleEventsEliminator.eliminate(labeled_signal)
    raw_series = ActionsClassifier.apply(labeled_signal)
    raw = IRRawSignal.from_labeled_signal(labeled_signal, raw_series)
    EDFAnnotationChannelAppender.apply(target_file_name, target_file_name, raw)


if __name__ == '__main__':
    edf_files = list_all_files(DATA_DIR)
    print('Need to annotate {} EDF files'.format(len(edf_files)))

    # Unskip ONLY if you are sure about annotation logic - this will change database!
    for i, edf_file in enumerate(edf_files):
        print('{}/{}. File: {}'.format(i+1, len(edf_files), edf_file))
        annotate_single_file(edf_file)
