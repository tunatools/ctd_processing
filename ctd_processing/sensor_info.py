import pandas as pd
import openpyxl
from pathlib import Path
import numpy as np


class InstrumentFile:
    def __init__(self, file_path):
        self.file_path = Path(file_path)

        self.wb = openpyxl.load_workbook(self.file_path)
        self.sheets = self.wb.sheetnames

        self.sbe_instrument_info = {}

        self._save_seabird_instrument_info()

    def _save_seabird_instrument_info(self):
        self.sbe_instrument_info = {}
        for sheet in self.sheets:
            if 'SBE' not in sheet:
                continue
            if 'CAT' in sheet:
                continue
            df = pd.read_excel(self.file_path, sheet_name=sheet, engine='openpyxl')
            for model, serial_nr in zip(df['Model'], df['Serial number']):
                model = str(model).replace(' ', '')
                serial_nr = str(serial_nr)
                if serial_nr == 'nan':
                    continue
                self.sbe_instrument_info.setdefault(serial_nr, {})
                self.sbe_instrument_info[serial_nr] = {'model': model,
                                                       'sensor_id': serial_nr,
                                                       'parameter': model}


if __name__ == '__main__':
    file_path = r'C:\mw\temp_svea\temp_filer/Instruments.xlsx'
    # e = pd.read_excel(r'C:\mw\temp_svea\temp_filer/Instruments.xlsx', engine='openpyxl')
    # e = openpyxl.load_workbook(file_path)
    # df = pd.read_excel(file_path, sheet_name='SBE Dissolved Oxygen Sensors', engine='openpyxl')

    ii = InstrumentFile(file_path)
