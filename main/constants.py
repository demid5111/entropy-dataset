import enum
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DATA_ROOT_DIR = os.path.join(ROOT_DIR, 'data')
GDRIVE_DATA_DIR = os.path.join(DATA_ROOT_DIR, 'rats_2018_gdrive')
DATA_DIR = GDRIVE_DATA_DIR  # os.path.join(DATA_ROOT_DIR, 'rats_2018')
TEST_DIR = os.path.join(DATA_ROOT_DIR, 'test')
TEST_REFERENCE_DIR = os.path.join(DATA_ROOT_DIR, 'test_references')
ARTIFACTS_DIR = os.path.join(DATA_ROOT_DIR, 'artifacts')
DATASETS_GDRIVE_FOLDER_NAME = 'rats_2018_behaviour'  # 'rats_2018_ECG_postprocessed' # 'rats_2018'
SECRETS_DIR = os.path.join(ROOT_DIR, 'secrets')

class ChannelsEnum(enum.Enum):
    eeg_ad_1 = 'AD1'
    eeg_ad_2 = 'AD2'
    eeg_ad_3 = 'AD3'
    ecg = 'AD4'
    behavior_class = 'Classes'
    behavior = 'IR'
