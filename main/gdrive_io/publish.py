import sys
from pathlib import Path

from googleapiclient.http import MediaFileUpload

from main.constants import GDRIVE_DATA_DIR
from main.dataset.generation.traverse_files import walk_through_collected_raw_data, SingleEntry
from main.gdrive_io.common import new_service, find_dataset_folder_gdrive_id, list_folder


def create_folder(drive_service, parent_folder_id, folder_name):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    return drive_service.files().create(body=file_metadata, fields='id').execute()


def create_file(drive_service, source_file_path: Path, parent_folder_id):
    file_metadata = {
        'name': source_file_path.name,
        'parents': [parent_folder_id]
    }
    media = MediaFileUpload(source_file_path)
    file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    return file


def update_file(drive_service, source_file_path: Path, file_id):
    media = MediaFileUpload(source_file_path)
    file = drive_service.files().update(fileId=file_id,
                                        media_body=media,
                                        fields='id').execute()
    return file


def entry_exists(drive_service, parent_folder_id, name):
    files = list_folder(drive_service=drive_service, folder_id=parent_folder_id, folder_name=None)
    entry = None
    for f in files:
        if f.get('name') == name:
            entry = f
            break
    return entry


def main():
    service = new_service()

    dataset_gdrive_folder_id = find_dataset_folder_gdrive_id(drive_service=service)
    if dataset_gdrive_folder_id is None:
        print('Unable to find dataset folder.')
        sys.exit(1)

    res = walk_through_collected_raw_data(GDRIVE_DATA_DIR)

    created = {}
    entry: SingleEntry
    for entry_index, entry in enumerate(res):
        rat_folder_exists = entry.rat_id in created
        if not rat_folder_exists:
            rat_folder = entry_exists(service, dataset_gdrive_folder_id, entry.rat_id)
            if not rat_folder:
                rat_folder = create_folder(service, dataset_gdrive_folder_id, entry.rat_id)
            created[entry.rat_id] = {}
            created[entry.rat_id]['folders'] = {}
            created[entry.rat_id]['id'] = rat_folder.get('id')

        experiment_folder_exists = entry.experiment_day in created[entry.rat_id]['folders']
        if not experiment_folder_exists:
            experiment_folder = entry_exists(service, created[entry.rat_id]['id'], entry.experiment_day)
            if not experiment_folder:
                experiment_folder = create_folder(service, created[entry.rat_id]['id'], entry.experiment_day)
            created[entry.rat_id]['folders'][entry.experiment_day] = experiment_folder.get('id')

        folder_id = created[entry.rat_id]['folders'][entry.experiment_day]
        source_path = Path(entry.file_path)
        file_exists = entry_exists(drive_service=service, parent_folder_id=folder_id, name=source_path.name)

        if file_exists:
            print(f'Skipping uploading of {source_path} as it already exists...')
        else:
            print(f'Uploading {source_path} {entry_index + 1}/{len(res)} ...')
            create_file(drive_service=service,
                        source_file_path=source_path,
                        parent_folder_id=folder_id)

    root_path = Path(GDRIVE_DATA_DIR)
    force_upload = ['dataset_versions.md']
    entries = [e for e in root_path.iterdir() if e.is_file()]
    e: Path
    for e in entries:
        file_exists = entry_exists(drive_service=service, parent_folder_id=dataset_gdrive_folder_id, name=e.name)
        if file_exists and e.name not in force_upload:
            print(f'Skipping uploading of {e.name} as it already exists...')
            continue
        elif file_exists and e.name in force_upload:
            print(f'Force refresh of {e.name} ...')
            update_file(drive_service=service,
                        source_file_path=e,
                        file_id=file_exists.get('id'))
        else:
            print(f'Uploading {e.name} ...')
            create_file(drive_service=service,
                        source_file_path=e,
                        parent_folder_id=dataset_gdrive_folder_id)


if __name__ == '__main__':
    main()
