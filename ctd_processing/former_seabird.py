import codecs
import datetime
import os
from pathlib import Path
import shutil

from ctd_processing import exceptions

from ctd_processing.former_ship import SHIPS


class SeabirdRawFileBase:
    def __init__(self, file_path, **kwargs):
        self.file_suffix = ''

        self.file_path = None
        self.file_name = None
        self.file_stem = None
        self.directory = None
        self._save_file_path_info(file_path)

        self.ship_id = None
        self.ctry = None
        self.ship = None
        self.ship_short_name = None
        self.serial_number = None

        self._load_ship()
        self._load_ship_info()

    def __repr__(self):
        return f'Seabird {self.file_suffix}-file: {self.file_path}'

    def _save_file_path_info(self, file_path):
        self.file_path = Path(file_path)
        self.file_name = self.file_path.name
        self.file_stem = self.file_path.stem
        self.directory = self.file_path.parent

    def _check_validity(self):
        if self.file_path.suffix != self.file_suffix:
            raise exceptions.PathError(f'Not a {self.file_suffix}-file')

    def _load_ship(self):
        fstem = self.file_stem.upper()
#        if fstem.startswith('SBE09'):
#            self.ship = ctd_processing.ship.get_ship_object_from_sbe09(fstem)
#            return
        for short_name, ship_object in SHIPS.items():
            if fstem.startswith(short_name):
                self.ship = ship_object(fstem=fstem)
                return
        raise exceptions.UnrecognizedFileName(self.file_path)

    def _load_ship_info(self):
        self.serial_number = self.ship.serial_number
        self.ship_short_name = self.ship.short_name
        self.ship_id = self.ship.ship_id
        self.ctry, self.ship = self.ship.ship_id.split('_')

    def rename(self, new_file_stem, overwrite=False):
        if new_file_stem == self.file_stem:
            return
        new_file_path = Path(self.directory, new_file_stem + self.file_suffix)
        if new_file_path.exists():
            if not overwrite:
                raise exceptions.FileExists(new_file_path)
            else:
                os.remove(new_file_path)
        os.rename(self.file_path, new_file_path)
        self._save_file_path_info(new_file_path)

    def move_file(self, directory, overwrite=False):
        new_file_path = Path(directory, self.file_name)
        if new_file_path.exists():
            if not overwrite:
                raise exceptions.FileExists(new_file_path)
            else:
                os.remove(new_file_path)
        shutil.move(str(self.file_path), str(directory))
        self._save_file_path_info(new_file_path)


class BlFile(SeabirdRawFileBase):
    def __init__(self, file_path, **kwargs):
        super().__init__(file_path, **kwargs)
        self.file_suffix = '.bl'

        self.number_of_bottles = None

        self._check_validity()
        self._save_number_of_bottles()

    def _save_number_of_bottles(self):
        self.number_of_bottles = 0
        with open(self.file_path) as fid:
            for nr, line in enumerate(fid):
                stripped_line = line.strip()
                if nr > 1 and stripped_line:
                    self.number_of_bottles += 1


class BtlFile(SeabirdRawFileBase):
    def __init__(self, file_path, **kwargs):
        super().__init__(file_path, **kwargs)
        self.file_suffix = '.btl'
        self._check_validity()


class HdrFile(SeabirdRawFileBase):
    def __init__(self, file_path, **kwargs):
        super().__init__(file_path, **kwargs)
        self.file_suffix = '.hdr'

        self.date_format_in_file = '%b %d %Y %H:%M:%S'

        self.date = None
        self.datum = None
        self.tid = None
        self.new_file_stem = None

        self.ctd = kwargs.get('ctd')

        self._check_validity()
        self._get_info_from_file()
        self._save_new_file_stem()

    def _get_info_from_file(self):
        with codecs.open(self.file_path, encoding='cp1252') as fid:
            for row in fid:
                if '* System UpLoad Time' in row:
                    # self.date_string = row[23:40]
                    date_string = row.split('=')[-1].strip()
                    self.date = datetime.datetime.strptime(date_string, self.date_format_in_file)
                if '** Station:' in row:
                    self.station_name = row.split(':')[-1].strip()
                    self.station_name = self.station_name.replace(' ', '_')
                    self.station_name = self.station_name.replace('/', '-')

    def _save_new_file_stem(self):
        date = self.date.strftime("%Y%m%d_%H%M")
        self.new_file_stem = f'SBE09_{self.ctd}_{date}_{self.ship_id}_{self.serial_number}'
        self.datum, self.tid = date.split('_')

    def validate_new_file_stem(self, stem):
        def _check_instrument_name(name):
            if name != 'SBE09':
                raise exceptions.InvalidInstrumentName(name)

        def _check_instrument_serial_number(nr):
            if nr not in ['0745', '1044', '0817', '0403', '0827', '1387']:
                raise exceptions.InvalidInstrumentSerialNumber

        def _check_date_format(date_str):
            if len(date_str) != 8 or not date_str.isdigit():
                raise exceptions.InvalidDateFormat

        def _check_time_format(time_str):
            if len(time_str) != 4 or not time_str.isdigit():
                raise exceptions.InvalidDateFormat

        def _check_country_code(code):
            pass

        def _check_ship_code(code):
            pass

        def _check_serial_number(nr):
            if len(nr) != 4:
                raise exceptions.InvalidSerialNumber

        try:
            name, inst_nr, date_str, time_str, ctry_code, ship_code, serno = stem.split('_')
        except:
            raise exceptions.InvalidFileNameFormat

        _check_instrument_name(name)
        _check_instrument_serial_number(inst_nr)
        _check_date_format(date_str)
        _check_time_format(time_str)
        _check_country_code(ctry_code)
        _check_ship_code(ship_code)
        _check_serial_number(serno)


class HexFile(SeabirdRawFileBase):
    def __init__(self, file_path, **kwargs):
        super().__init__(file_path, **kwargs)
        self.file_suffix = '.hex'
        self._check_validity()


class RosFile(SeabirdRawFileBase):
    def __init__(self, file_path, **kwargs):
        super().__init__(file_path, **kwargs)
        self.file_suffix = '.ros'
        self._check_validity()


class XmlconFile(SeabirdRawFileBase):
    def __init__(self, file_path, **kwargs):
        super().__init__(file_path, **kwargs)
        self.file_suffix = '.XMLCON'
        self._check_validity()


class ConFile(SeabirdRawFileBase):
    def __init__(self, file_path, **kwargs):
        super().__init__(file_path, **kwargs)
        self.file_suffix = '.CON'
        self._check_validity()


class SeabirdFiles:
    file_classes = {'.bl': BlFile,
                    '.btl': BtlFile,
                    '.hdr': HdrFile,
                    '.hex': HexFile,
                    '.ros': RosFile,
                    '.XMLCON': XmlconFile,
                    '.CON': ConFile}

    def __init__(self, file_path, ctd):
        """
        :param file_path: any file with extension listed in cls.file_classes
        """
        file_path = Path(file_path)
        self.directory = file_path.parent
        self.file_stem = file_path.stem

        self.ctd = str(ctd)

        self.serial_number = None
        self.ship_short_name = None
        self.ship_id = None
        self.ctry = None
        self.ship = None
        self.new_file_stem = None
        self.station_name = None
        self.number_of_bottles = None

        self.files = {}
        self._load_files()
        self._load_info()

    def __repr__(self):
        return_list = ['Seabird files:']
        for key, value in self.files.items():
            return_list.append(f'{key}-file: {value}')
        return '\n'.join(return_list)

    def _load_files(self):
        for file_path in self.directory.iterdir():
            if file_path.stem == self.file_stem:
                suffix = file_path.suffix
                file_class = self.file_classes.get(suffix)
                self.files[suffix] = file_class(file_path, ctd=self.ctd)

    def _load_info(self):
        self.serial_number = self.files['.hdr'].serial_number
        self.ship_short_name = self.files['.hdr'].ship_short_name
        self.ship_id = self.files['.hdr'].ship_id
        self.ctry = self.files['.hdr'].ctry
        self.ship = self.files['.hdr'].ship
        self.date = self.files['.hdr'].date
        self.new_file_stem = self.files['.hdr'].new_file_stem
        self.datum = self.files['.hdr'].datum
        self.tid = self.files['.hdr'].tid
        self.station_name = self.files['.hdr'].station_name
        self.number_of_bottles = self.files['.bl'].number_of_bottles

    def rename_files(self, overwrite=False):
        """
        Renames the files to the new file stem.
        :return:
        """
        for file in self.files.values():
            file.rename(self.new_file_stem, overwrite=overwrite)

    def move_files(self, directory, overwrite=False):
        directory = Path(directory)
        if not directory.exists():
            os.makedirs(directory)
        for file in self.files.values():
            file.move_file(directory, overwrite=overwrite)
        self.directory = directory


if __name__ == '__main__':
    s = SeabirdFiles(r'C:\mw\data\sbe_raw_files/SBE09_1387_20200816_1346_77_10_0497.bl', ctd='1387')


