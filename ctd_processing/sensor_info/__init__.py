import pathlib
from .func import get_sensor_info_columns

from .instrument_file import InstrumentFile
from .sensor_info_file import SensorInfoFile


def create_sensor_info_files_from_cnv_files_in_directory(directory, instrument_file_path, output_dir=None):
    sensor_info = get_sensor_info_object(instrument_file_path)
    for path in pathlib.Path(directory).iterdir():
        if not path.suffix == '.cnv':
            continue
        sensor_info.create_file_from_cnv_file(path, output_dir)

def create_sensor_info_files_from_cnv_files(cnv_files, instrument_file_path, output_dir=None):
    sensor_info = get_sensor_info_object(instrument_file_path)
    for path in cnv_files:
        if not path.suffix == '.cnv':
            continue
        sensor_info.create_file_from_cnv_file(path, output_dir=output_dir)


def get_sensor_info_object(instrumentinfo_file):
    instrument_file = InstrumentFile(instrumentinfo_file)
    sensor_info = SensorInfoFile(instrument_file)
    return sensor_info