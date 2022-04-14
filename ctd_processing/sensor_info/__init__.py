import pathlib
from .func import get_sensor_info_columns

from .instrument_file import InstrumentFile
from .sensor_info_file import CreateSensorInfoFile
from .sensor_info_file import CreateSensorInfoSummaryFile

import logging

logger = logging.getLogger(__name__)


def create_sensor_info_files_from_cnv_files_in_directory(directory, instrument_file_path, output_dir=None):
    sensor_info = get_sensor_info_object(instrument_file_path)
    for path in pathlib.Path(directory).iterdir():
        if not path.suffix == '.cnv':
            continue
        sensor_info.create_file_from_cnv_file(path, output_dir)


def create_sensor_info_files_from_cnv_files(cnv_files, instrument_file_path):
    sensor_info = get_sensor_info_object(instrument_file_path)
    for path in cnv_files:
        if not path.suffix == '.cnv':
            continue
        sensor_info.create_file_from_cnv_file(path)


def create_sensor_info_files_from_package(pack, instrument_file_path):
    cnv = pack.get_file_path(suffix='.cnv', prefix=None)
    if not cnv:
        FileNotFoundError(f'Could not find cnv file for package: {pack.key}')
    create_sensor_info_files_from_cnv_files([cnv], instrument_file_path)


def get_sensor_info_object(instrumentinfo_file):
    if isinstance(instrumentinfo_file, InstrumentFile):
        inst_file = instrumentinfo_file
    else:
        inst_file = InstrumentFile(instrumentinfo_file)
    sensor_info = CreateSensorInfoFile(inst_file)
    return sensor_info


def create_sensor_info_summary_file_from_directory(directory, output_directory=None):
    sensorinfo = CreateSensorInfoSummaryFile(directory)
    return sensorinfo.write_summary_to_file(directory=output_directory)