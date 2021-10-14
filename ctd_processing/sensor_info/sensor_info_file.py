import pathlib

from .instrument_file import InstrumentFile
from .sensor_info_item import SensorInfoItem
from . import get_sensor_info_columns

from ctd_processing import cnv
from ctd_processing import xmlcon
from ctd_processing import ctd_files


class SensorInfoFile:
    def __init__(self, instrument_file: InstrumentFile):
        self.instrument_file = instrument_file
        self._stem = None
        self._save_path = None
        self._data = None

    def __str__(self):
        return f'SensorInfoFile: {self._stem}'

    def create_file_from_cnv_file(self, cnv_file_path):
        """
        Created a sensor info file with information in given cnv file.
        The sensor info file is created at the same location as the cnv file.
        """
        path = pathlib.Path(cnv_file_path)
        print(path)
        self._stem = path.stem
        self._save_path = pathlib.Path(path.parent, f'{self._stem}.sensorinfo')
        self._save_data_from_cnv(path)
        self._save_file()

    def _save_data_from_cnv(self, path):
        self._data = []
        cnv_info = xmlcon.CNVfileXML(path).get_sensor_info()
        channel_mapping = cnv.get_sensor_id_and_paramater_mapping_from_cnv(path)
        ctd_file_obj = ctd_files.get_ctd_files_object(path)

        instrument = path.name.split('_')[0]
        columns = [col for col in get_sensor_info_columns() if col not in ['VALIDFR', 'VALIDTO']]
        self._data.append('\t'.join(columns))
        for info in cnv_info:
            row_list = []
            instrument_info = self.instrument_file.get_info_for_parameter_and_sensor_id(parameter=info['parameter'],
                                                                                        sensor_id=info['serial_number'])
            if not instrument_info:
                #print('NOT', info['serial_number'], info['parameter'])
                continue
            for col in columns:
                value = str(instrument_info.get(col, ''))
                if col == 'SENSOR_ID':
                    value = info['serial_number']
                elif col == 'CALIB_DATE':
                    value = info['calibration_date'].strftime('%Y-%m-%d')
                elif value:
                    if col == 'PARAMETER_REPORTED':
                        value = channel_mapping.get(info['serial_number'])
                    if info['parameter'][-1] == '2':
                        if col == 'PARAM_SIMPLE':
                            value = value + '2'
                        elif col == 'PARAM':
                            split_value = value.split('_')
                            split_value[-2] = split_value[-2] + '2'
                            value = '_'.join(split_value)
                else:
                    if col == 'INSTRUMENT_ID':
                        value = instrument + ctd_file_obj.instrument_number
                    elif col == 'INSTRUMENT_PROD':
                        if instrument.startswith('SBE'):
                            value = 'Seabird'
                    elif col == 'INSTRUMENT_MOD':
                        value = '911plus'
                    elif col == 'INSTRUMENT_SERIE':
                        value = ctd_file_obj.instrument_number
                    elif col == 'TIME':
                        value = ctd_file_obj.time.strftime('%Y-%m-%d')

                row_list.append(value)
            self._data.append('\t'.join(row_list))

    def _save_file(self):
        with open(self._save_path, 'w') as fid:
            fid.write('\n'.join(self._data))


class SensorInfoFiles:

    def __init__(self, directory):
        self._directory = pathlib.Path(directory)
        self._paths = [path for path in self._directory.iterdir() if path.suffix == '.sensorinfo']
        self._sensor_info_items = {}
        self._save_info()

    def _save_info(self):
        self._sensor_info_items = {}
        for path in self._paths:
            header = None
            with open(path) as fid:
                for r, line in enumerate(fid):
                    split_line = [item.strip() for item in line.strip().split('\t')]
                    if r == 0:
                        header = split_line
                        continue
                    data = dict(zip(header, split_line))
                    key = SensorInfoItem.get_key(data)
                    obj = self._sensor_info_items.setdefault(key, SensorInfoItem())
                    obj.add_data(data)

    def write_to_file(self):
        path = pathlib.Path(self._directory, 'sensorinfo.txt')
        columns = get_sensor_info_columns()
        lines = []
        lines.append('\t'.join(columns))
        for key in sorted(self._sensor_info_items):
            info = self._sensor_info_items[key].get_info()
            lines.append('\t'.join([info.get(col, '') for col in columns]))

        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))