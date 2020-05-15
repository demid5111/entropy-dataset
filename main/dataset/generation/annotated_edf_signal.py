from main.constants import ChannelsEnum
from main.models.raw_signal import RawSignal


class AnnotatedEDFSignal:
    labels = (
        ChannelsEnum.eeg_ad_1.value,
        ChannelsEnum.eeg_ad_2.value,
        ChannelsEnum.eeg_ad_3.value,
        ChannelsEnum.behavior_class.value
    )

    def __init__(self):
        self.eeg_ad_1 = None

    @classmethod
    def from_edf_file(cls, edf_file_path):
        signal = AnnotatedEDFSignal()
        signal.eeg_ad_1 = RawSignal.from_edf(edf_file_path, ChannelsEnum.eeg_ad_1.value)
        signal.eeg_ad_2 = RawSignal.from_edf(edf_file_path, ChannelsEnum.eeg_ad_2.value)
        signal.eeg_ad_3 = RawSignal.from_edf(edf_file_path, ChannelsEnum.eeg_ad_3.value)
        signal.behavior_class = RawSignal.from_edf(edf_file_path, ChannelsEnum.behavior_class.value)
        return signal
