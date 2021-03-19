import io
import shutil
import sys
from pathlib import Path

from googleapiclient.http import MediaIoBaseDownload

from main.constants import GDRIVE_DATA_DIR
from main.gdrive_io.common import find_dataset_folder_gdrive_id, list_folder, new_service

SKIP_DOWNLOAD = False
FRESH_DOWNLOAD = True


def log_grive_entry(gdrive_entry, current_index, total_entries_len, indent):
    index_printed = f'{current_index + 1}/{total_entries_len}'
    print(f'{"  " * indent}title: {gdrive_entry["name"]}; id: {gdrive_entry["id"]}; {index_printed}')


def download_file(drive_service, file_id, save_path, indent):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(save_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f'{"  " * indent}Download: {int(status.progress() * 100)}%')


def is_folder(gdrive_entry):
    return gdrive_entry.get('mimeType') == 'application/vnd.google-apps.folder'


if __name__ == '__main__':
    service = new_service()

    dataset_gdrive_folder_id = find_dataset_folder_gdrive_id(drive_service=service)
    if dataset_gdrive_folder_id is None:
        print('Unable to find dataset folder.')
        sys.exit(1)

    if FRESH_DOWNLOAD:
        try:
            shutil.rmtree(GDRIVE_DATA_DIR)
        except FileNotFoundError:
            print('No such directory, skipping its creation')

    all_files_to_download = list_folder(drive_service=service, folder_id=dataset_gdrive_folder_id)
    rat_list = [i for i in all_files_to_download if is_folder(i)]
    other_files = [i for i in all_files_to_download if not is_folder(i)]
    for rat_index, rat_object in enumerate(rat_list):
        level = 0
        log_grive_entry(rat_object, rat_index, len(rat_list), level)
        rat_experiments = list_folder(drive_service=service, folder_id=rat_object['id'])

        for rat_experiment_index, rat_experiment in enumerate(rat_experiments):
            level = 1
            log_grive_entry(rat_experiment, rat_experiment_index, len(rat_experiments), level)
            experiment_artifacts = list_folder(drive_service=service, folder_id=rat_experiment['id'])

            for experiment_artifact_index, experiment_artifact in enumerate(experiment_artifacts):
                if experiment_artifact['mimeType'] == 'application/vnd.google-apps.folder':
                    path = f'{rat_object["name"]}/{rat_experiment["name"]}/{experiment_artifact["name"]}'
                    print(f'WARNING: Ignoring {path}')
                    continue
                level = 2
                log_grive_entry(experiment_artifact, experiment_artifact_index, len(experiment_artifacts), level)
                print(f'{"  " * level}downloading {experiment_artifact["name"]} ...')

                directory_path = Path(GDRIVE_DATA_DIR) / rat_object['name'] / rat_experiment['name']
                try:
                    directory_path.mkdir(parents=True)
                except FileExistsError:
                    pass
                save_path = directory_path / experiment_artifact['name']

                if SKIP_DOWNLOAD:
                    print(f'{"  " * level}Skipping download. Change SKIP_DOWNLOAD to False to start.')
                elif save_path.exists():
                    print(f'{"  " * level}Skipping download {save_path} as file exists')
                else:
                    download_file(drive_service=service,
                                  file_id=experiment_artifact.get('id'),
                                  save_path=save_path,
                                  indent=level)

    for other_file in other_files:
        level = 0
        save_path = Path(GDRIVE_DATA_DIR) / other_file['name']

        if SKIP_DOWNLOAD:
            print(f'{"  " * level}Skipping download. Change SKIP_DOWNLOAD to False to start.')
        elif save_path.exists():
            print(f'{"  " * level}Skipping download {other_file["name"]} as file exists')
        else:
            print(f'{"  " * level}downloading {other_file["name"]} ...')
            download_file(drive_service=service,
                          file_id=other_file.get('id'),
                          save_path=save_path,
                          indent=level)
