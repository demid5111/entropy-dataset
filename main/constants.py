import enum
import os


DATA_ROOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'data')
DATA_DIR = os.path.join(DATA_ROOT_DIR, 'rats_2018')
TEST_DIR = os.path.join(DATA_ROOT_DIR, 'test')
ARTIFACTS_DIR = os.path.join(DATA_ROOT_DIR, 'artifacts')


class ChannelsEnum(enum.Enum):
    eeg_ad_1 = 'AD1'
    eeg_ad_2 = 'AD2'
    eeg_ad_3 = 'AD3'
    ecg = 'AD4'
    behavior_class = 'Classes'
    behavior = 'IR'
