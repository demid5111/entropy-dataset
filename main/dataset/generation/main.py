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

        path_wo_ext, ext = os.path.splitext(os.path.relpath(desc.file_path, root_path).replace('/', '_'))
        if ext.lower() != '.edf':
            print(f'Ignoring <{desc.file_path}> as not edf file...')
            continue

        df_file_name = path_wo_ext + '.xlsx'
        df_path = os.path.join(tmp_df_dir, df_file_name)

        mapping: StageMapping = StageMapping(os.path.join(root_path, 'learning_stages_rat_date.xlsx'),
                                             desc.rat_id,
                                             desc.experiment_day)

        if os.path.exists(df_path):
            print(f'Skipping <{desc.file_path}> as already processed...')
            dataset_df = read_dataset(df_path)
        else:
            dataset_df = extract_all_acts_from_single_file(rat_id=desc.rat_id,
                                                           experiment_number=mapping.experiment_number,
                                                           learning_stage_id=mapping.learning_stage_id,
                                                           learning_stage_description=mapping.learning_stage_description,
                                                           file_path=desc.file_path)
        if not dataset_df.empty:
            all_datasets.append(dataset_df)
            save_dataset(df_path, dataset_df)
    return pd.concat(all_datasets)


def save_dataset(destination_path, df):
    writer = pd.ExcelWriter(destination_path, engine='xlsxwriter')
    sheet_name = 'Dataset'
    df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=1)  # send df to writer

    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    for idx, col in enumerate(df):  # loop through all columns
        series = df[col]
        max_len = max((
            series.astype(str).map(len).max(),  # len of largest item
            len(str(series.name))  # len of column name/header
        )) + 1  # adding a little extra space
        mapping = {
            1: 25,
            4: 18,
            6: 25,
            7: 25,
            8: 11,
            9: 11,
            10: 11,
            14: 11,
            15: 11
        }
        worksheet.set_column(idx, idx, width=mapping.get(idx, max_len // 2))

    # Add a header format.
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'border': 1})

    # Write the column headers with the defined format.
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    writer.save()


def read_dataset(destination_path):
    df = pd.read_excel(destination_path)  # send df to writer
    return df
