import pathlib
import datetime

# from .instrument_file import InstrumentFile
from .sensor_info_item import SensorInfoItem
from .func import get_sensor_info_columns

from ctd_processing import cnv
from ctd_processing import xmlcon
from ctd_processing import ctd_files
from ctd_processing.sensor_info import param_reported


class SensorInfoFile:
    def __init__(self, instrument_file):
        self.instrument_file = instrument_file
        self._stem = None
        self._save_path = None
        self._data = None

    def __str__(self):
        return f'SensorInfoFile: {self._stem}'

    def create_file_from_cnv_file(self, cnv_file_path, output_dir=None):
        """
        Created a sensor info file with information in given cnv file.
        The sensor info file is created at the same location as the cnv file.
        """
        path = pathlib.Path(cnv_file_path)
        self._stem = path.stem
        if not output_dir:
            output_dir = path.parent
        self._save_path = pathlib.Path(output_dir, f'{self._stem}.sensorinfo')
        self._save_xml_data_from_cnv(path)
        self._save_file()

    def _save_xml_data_from_cnv(self, path):
        self._data = []
        self.cnv_info = xmlcon.CNVfileXML(path).get_sensor_info()
        self._add_header_information_to_cnv_info(path)
        # channel_mapping = cnv.get_sensor_id_and_parameter_mapping_from_cnv(path)
        # print('channel_mapping', channel_mapping)
        ctd_file_obj = ctd_files.get_ctd_files_object(path)

        par_reported = param_reported.ParamReported(path, self.instrument_file)

        instrument = path.name.split('_')[0]
        columns = [col for col in get_sensor_info_columns() if col not in ['VALIDFR', 'VALIDTO']]
        self._data.append('\t'.join(columns))
        for info in self.cnv_info:
            # if info['parameter'] != 'sal11':
            #     continue
            print('='*50)
            print(info['parameter'])
            print('-' * 50)
            row_list = []
            instrument_info = self.instrument_file.get_info_for_parameter_and_sensor_id(parameter=info['parameter'],
                                                                                        sensor_id=info['serial_number'])
            if not instrument_info:
                print('NOT', info['serial_number'], info['parameter'])
                continue
            print('instrument_info', instrument_info)
            for col in columns:
                # print('col', col)
                value = str(instrument_info.get(col, ''))
                if col == 'SENSOR_ID':
                    value = info.get('serial_number', '')
                    if value is None:
                        value = ''
                elif col == 'CALIB_DATE':
                    value = info.get('calibration_date', '')
                    if value:
                        value = value.strftime('%Y-%m-%d')
                elif col == 'PARAM_REPORTED':
                    value = par_reported.get_reported_name(info['parameter'], info['serial_number'])
                    print('value:PARAM_REPORTED', value, info['parameter'])
                elif value:
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

    def _add_header_information_to_cnv_info(self, path):
        names = cnv.get_reported_names_in_cnv(path)
        for name in names:
            cnv_code = name.split(':')[0].strip()
            info = {'parameter': cnv_code,
                    'serial_number': None}
            self.cnv_info.append(info)

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
                    # obj = self._sensor_info_items.setdefault(key, SensorInfoItem())
                    # obj.add_data(data)
                    # =============================
                    print('key', key)
                    par = key[1]
                    self._sensor_info_items.setdefault(par, [])
                    if not self._sensor_info_items[par] or self._sensor_info_items[par][-1]['key'] != key:
                        self._sensor_info_items[par].append(dict(key=key,
                                                                 obj=SensorInfoItem()))
                    self._sensor_info_items[par][-1]['obj'].add_data(data)

    def write_summary_to_file(self, directory=None):
        if not directory:
            directory = self._directory
        path = pathlib.Path(directory, 'sensorinfo.txt')
        columns = get_sensor_info_columns()
        lines = []
        lines.append('\t'.join(columns))
        for par in sorted(self._sensor_info_items):
            for item in self._sensor_info_items[par]:
                info = item['obj'].get_info()
                lines.append('\t'.join([info.get(col, '') for col in columns]))

        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))
        return path

    def old_write_summary_to_file(self, directory=None):
        if not directory:
            directory = self._directory
        path = pathlib.Path(directory, 'sensorinfo.txt')
        columns = get_sensor_info_columns()
        lines = []
        lines.append('\t'.join(columns))
        for key in sorted(self._sensor_info_items):
            info = self._sensor_info_items[key].get_info()
            lines.append('\t'.join([info.get(col, '') for col in columns]))

        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))

