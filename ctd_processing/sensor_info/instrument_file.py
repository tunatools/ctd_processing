import pandas as pd
import pathlib
import openpyxl


class InstrumentFile:
    def __init__(self, file_path):
        self._path = pathlib.Path(file_path)

        self._wb = openpyxl.load_workbook(self._path)
        self._sheets = self._wb.sheetnames

        self._info = {}

        self._save_info()

    def __str__(self):
        return f'InstrumentFile: {self._path}'

    def _save_info(self):
        self._info = {}
        # df = pd.read_excel(self._path, sheet_name='Instrument.xls', engine='openpyxl', skiprows=[0])
        df = pd.read_excel(self._path, sheet_name='Sensor_info', engine='openpyxl', skiprows=[0])
        df = df.fillna('')
        for i in df.index:
            cnv_name = str(df.iloc[i]['CNV_NAME'])
            if cnv_name == '':
                continue
            self._info.setdefault(cnv_name, {})
            sensor_string = str(df.iloc[i]['SENSOR_ID'])
            if sensor_string is '':
                self._info[cnv_name]['all'] = df.iloc[i].to_dict()
            else:
                sensor_list = [item.strip() for item in sensor_string.split(',')]
                for sensor in sensor_list:
                    self._info[cnv_name][sensor] = df.iloc[i].to_dict()

    def get_info_for_parameter_and_sensor_id(self, parameter, sensor_id):
        """ Returns information from self._info. Matches key in self._info where key is part of "parameter" """
        for key, info in self._info.items():
            if key in parameter:
                return info.get(str(sensor_id))
