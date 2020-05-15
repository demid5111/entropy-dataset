from main.constants import ChannelsEnum
from main.models.raw_signal import RawSignal


class IRRawSignal(RawSignal):
    edf_label = ChannelsEnum.behavior.value
