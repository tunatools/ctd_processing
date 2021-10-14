import pathlib

from .instrument_file import InstrumentFile
from .sensor_info_file import SensorInfoFile
from .sensor_info_file import SensorInfoFiles


def get_sensor_info_columns():
    path = pathlib.Path(pathlib.Path(__file__).parent, 'resources', 'sensor_info_columns.txt')
    columns = []
    with open(path) as fid:
        for line in fid:
            sline = line.strip()
            if not sline:
                continue
            columns.append(sline)
    return columns


def get_sensor_info_object(instrumentinfo_file):
    instrument_file = InstrumentFile(instrumentinfo_file)
    sensor_info = SensorInfoFile(instrument_file)
    return sensor_info


def create_sensor_info_files_in_cnv_directory(directory, instrument_file_path):
    sensor_info = get_sensor_info_object(instrument_file_path)
    for path in pathlib.Path(directory).iterdir():
        if not path.suffix == '.cnv':
            continue
        sensor_info.create_file_from_cnv_file(path)
