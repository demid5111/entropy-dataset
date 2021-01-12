import os
from typing import List

import pandas as pd

from main.constants import ARTIFACTS_DIR
from main.dataset.generation.single_experiment import extract_all_acts_from_single_file
from main.dataset.generation.traverse_files import walk_through_collected_raw_data, SingleEntry, StageMapping


def collect_dataset_as_dataframe(root_path):
    meta_descriptors: List[SingleEntry] = walk_through_collected_raw_data(root_path)

    tmp_df_dir = os.path.join(ARTIFACTS_DIR, 'df')
    os.makedirs(tmp_df_dir, exist_ok=True)

    all_datasets = []
    for i, desc in enumerate(meta_descriptors):
        print(f'Processing {i + 1}/{len(meta_descriptors)}. Path: {desc.file_path}')
        df_file_name = os.path.splitext(os.path.relpath(desc.file_path, root_path).replace('/', '_'))[0] + '.xlsx'
        df_path = os.path.join(tmp_df_dir, df_file_name)
        if os.path.exists(df_path):
            print(f'Skipping <{desc.file_path}>...')
            continue

        mapping: StageMapping = StageMapping(os.path.join(root_path, 'learning_stages_rat_date.xlsx'),
                                             desc.rat_id,
                                             desc.experiment_day)
        dataset_df = extract_all_acts_from_single_file(rat_id=desc.rat_id,
                                                       experiment_number=mapping.experiment_number,
                                                       learning_stage_id=mapping.learning_stage_id,
                                                       learning_stage_description=mapping.learning_stage_description,
                                                       file_path=desc.file_path)
        all_datasets.append(dataset_df)
        save_dataset(df_path, dataset_df)
    return pd.concat(all_datasets)


def save_dataset(destination_path, df):
    df.index = df.index + 1
    df.to_excel(destination_path)
