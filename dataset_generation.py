import os
import sys

# absolutely needed due to the absolute imports of entropier and its usage as a submodule instead of a library
# should be at the top of the module
from main.constants import DATA_DIR, ROOT_DIR, ARTIFACTS_DIR

sys.path.insert(0, f'{ROOT_DIR}/main/entropier')

from main.dataset.generation.main import collect_dataset_as_dataframe, save_dataset

if __name__ == '__main__':
    df = collect_dataset_as_dataframe(DATA_DIR)

    save_dataset(os.path.join(ARTIFACTS_DIR, 'dataset.xlsx'), df)
