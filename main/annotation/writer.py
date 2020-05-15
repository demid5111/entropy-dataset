import pyedflib

from main.constants import ChannelsEnum


class EDFAnnotationChannelAppender:
    @staticmethod
    def apply(file_name, target_file_name, raw_signal):
        header_name = ChannelsEnum.behavior_class.value
        signals, signal_headers, header = pyedflib.highlevel.read_edf(file_name)
        classes_index = None
        for i, signal_header in enumerate(signal_headers):
            if signal_header['label'] == header_name:
                classes_index = i

        if classes_index is None:
            signals.append(raw_signal._data)
            class_header = pyedflib.highlevel.make_signal_header(label=header_name,
                                                                 sample_rate=raw_signal._ir_frequency,
                                                                 physical_min=-1,
                                                                 physical_max=1,
                                                                 digital_min=-1,
                                                                 digital_max=1)

            signal_headers.append(class_header)
        else:
            signals[classes_index] = raw_signal._data

        pyedflib.highlevel.write_edf(target_file_name, signals, signal_headers, header)
