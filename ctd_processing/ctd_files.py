from abc import ABC, abstractmethod
from pathlib import Path
import re
import codecs
import datetime
import os
import shutil

from ctd_processing import cnv


class BlFile:
    def __init__(self, file_path, **kwargs):
        if file_path.suffix != '.bl':
            raise Exception(f'Given file is not a .bl file: {file_path}')
        self.file_path = file_path

        self._number_of_bottles = None

        self._save_number_of_bottles()

    @property
    def number_of_bottles(self):
        return self._number_of_bottles

    def _save_number_of_bottles(self):
        self._number_of_bottles = 0
        with open(self.file_path) as fid:
            for nr, line in enumerate(fid):
                stripped_line = line.strip()
                if nr > 1 and stripped_line:
                    self._number_of_bottles += 1


class CnvFile:
    def __init__(self, file_path):
        self._path = Path(file_path)

        self.date_format_in_file = '%b %d %Y %H:%M:%S'
        self._time = None
        self._lat = None
        self._lon = None
        self._station = None
        self._get_info_from_file()

    def _get_info_from_file(self):
        with codecs.open(self._path, encoding='cp1252') as fid:
            for line in fid:
                if '* System UTC' in line:
                    self._time = datetime.datetime.strptime(line.split('=')[1].strip(), self.date_format_in_file)
                elif '* NMEA Latitude' in line:
                    self._lat = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif '* NMEA Longitude' in line:
                    self._lon = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('** Station'):
                    self._station = line.split(':')[-1].strip()

    @property
    def time(self):
        return self._time

    @property
    def lat(self):
        return self._lat

    @property
    def lon(self):
        return self._lon

    @property
    def station(self):
        return self._station


class HdrFile:
    def __init__(self, file_path):
        """

        :param file_path: pathlib.Path
        :param kwargs:
        """
        if file_path.suffix != '.hdr':
            raise Exception(f'Given file is not a .hdr file: {file_path}')
        self.file_path = file_path

        self.date_format_in_file = '%b %d %Y %H:%M:%S'

        self._station = None
        self._time = None
        self._cruise_number = '00'

        self._get_info_from_file()

    @property
    def station(self):
        return self._station

    @property
    def time(self):
        return self._time

    @property
    def cruise_number(self):
        return self._cruise_number

    def _get_info_from_file(self):
        with codecs.open(self.file_path, encoding='cp1252') as fid:
            for row in fid:
                if '* System UpLoad Time' in row:
                    # self.date_string = row[23:40]
                    date_string = row.split('=')[-1].strip()
                    self._time = datetime.datetime.strptime(date_string, self.date_format_in_file)
                elif '** Station:' in row:
                    self._station = row.split(':')[-1].strip().replace(' ', '_').replace('/', '-')
                elif '** Cruise:' in row:
                    self._cruise_number = row.split('-')[-1].zfill(2)


class CTDFiles(ABC):
    _original_file_path = None
    _files = {}
    _plot_files = []
    __proper_pattern = '[^_]+_\d{4}_\d{8}_\d{4}_\d{2}[a-zA-Z]{2}_\d{2}_\d{4}'

    def __str__(self):
        files = '\n'.join(sorted([f'  {str(path)}' for path in self._files.values()]))
        return f"""Instrument object for pattern {self.pattern}\nFiles: \n{files}"""

    def __repr__(self):
        files = '\n'.join(sorted([f'  {str(path)}' for path in self._files.values()]))
        return f"""Instrument object for pattern {self.pattern}\nFiles: \n{files}"""

    def __call__(self, key, *args, **kwargs):
        return self._files.get(key, None)

    @property
    @abstractmethod
    def raw_files_extensions(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def station(self):
        pass

    @property
    @abstractmethod
    def lat(self):
        pass

    @property
    @abstractmethod
    def lon(self):
        pass

    @property
    @abstractmethod
    def serno(self):
        pass

    @property
    @abstractmethod
    def time(self):
        pass

    @property
    @abstractmethod
    def year(self):
        pass

    @property
    @abstractmethod
    def pattern(self):
        pass

    @property
    @abstractmethod
    def pattern_example(self):
        pass

    @property
    @abstractmethod
    def instrument_number(self):
        pass

    @property
    @abstractmethod
    def file_path(self):
        pass

    @property
    def all_files(self):
        return self._files

    @property
    def plot_files(self):
        return self._plot_files

    @abstractmethod
    def _get_proper_file_stem(self):
        pass

    @property
    def proper_stem(self):
        stem = self._get_proper_file_stem()
        if not re.findall(self.__proper_pattern, stem):
            raise Exception(
                f'Invalid file_stem_pattern in file {self.file_path}. Pattern should be {self.__proper_pattern}')
        return stem

    @abstractmethod
    def add_processed_file_paths(self):
        pass

    @abstractmethod
    def _modify_and_save_cnv_file(self, save_directory=None, overwrite=False):
        pass

    def modify_and_save_cnv_file(self, save_directory=None, overwrite=False):
        self._modify_and_save_cnv_file(save_directory=save_directory, overwrite=overwrite)

    @property
    def stem(self):
        return self.file_path.stem

    @property
    def parent(self):
        return self.file_path.parent

    def has_file(self, suffix):
        if not self._files.get(suffix):
            return False
        return True

    def set_file_path(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        if not self._check_file_stem(file_path):
            raise Exception(f'File "{file_path}" does not match stem pattern "{self.pattern}"')
        self._original_file_path = file_path
        self._save_file_paths(file_path)

    def rename_files(self, overwrite=False):
        """ Rename the files so they get the proper file stem """
        new_files = {}
        for key, path in self._files.items():
            new_path = self._rename_file(path, overwrite=overwrite)
            new_files[key] = new_path
        self._files = new_files

    def _rename_file(self, path, overwrite=False):
        """ Rename a single file with the proper file stem """
        new_path = Path(path.parent, f'{self.proper_stem}{path.suffix}')
        if str(new_path) == str(path):
            return new_path
        if new_path.exists():
            if not overwrite:
                raise FileExistsError(new_path)
            os.remove(new_path)
        path.rename(new_path)
        return new_path

    def _check_file_stem(self, file_path):
        if re.findall(self.pattern, file_path.stem):
            return True
        return False

    def _save_file_paths(self, file_path):
        self._files = {}
        for path in file_path.parent.iterdir():
            if path.stem == file_path.stem:
                self._files[path.suffix] = path

    def is_valid(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            return False
        return self._check_file_stem(file_path)


class SBECTDFiles(CTDFiles):
    raw_files_extensions = ['.bl', '.btl', '.hdr', '.hex', '.ros', '.XMLCON', '.CON']

    @property
    @abstractmethod
    def config_file_suffix(self):
        pass

    def _check_hdr_file(self):
        if not self.has_file('.hdr'):
            raise FileNotFoundError('.hdr')

    @property
    def station(self):
        if self._files.get('.hdr'):
            obj = HdrFile(self._files['.hdr'])
        else:
            obj = CnvFile(self._files['.cnv'])
        return obj.station

    @property
    def serno(self):
        return self.stem.split('_')[-1]

    @property
    def lat(self):
        if not self._files.get('.cnv'):
            return None
        return CnvFile(self._files['.cnv']).lat

    @property
    def lon(self):
        if not self._files.get('.cnv'):
            return None
        return CnvFile(self._files['.cnv']).lon

    @property
    def time(self):
        if self._files.get('.hdr'):
            obj = HdrFile(self._files['.hdr'])
        else:
            obj = CnvFile(self._files['.cnv'])
        return obj.time

    @property
    def year(self):
        return self.time.year

    @property
    def number_of_bottles(self):
        obj = BlFile(self._files['.bl'])
        return obj.number_of_bottles

    @property
    def instrument_number(self):
        # Information not in file name in former raw files. Should be in child.
        return self.stem.split('_')[1]

    @property
    def file_path(self):
        path = self._files.get('.hex')
        if not path:
            return self._files.get('.cnv')
        return path

    def add_processed_file_paths(self):
        """ Adds files created by seasave. Saves filepaths with same file stem"""
        self._plot_files = []
        stem = self.stem.lower()
        for path in self.parent.iterdir():
            if stem not in str(path).lower():
                continue
            if path in self._files.values():
                continue
            if path.suffix == '.jpg':
                self._plot_files.append(path)
            elif path.suffix == '.cnv':
                if path.name.lower().startswith('sbe'):
                    self._files['cnv'] = path
                elif path.name.lower().startswith('u'):
                    self._files['cnv_up'] = path
                elif path.name.lower().startswith('d'):
                    self._files['cnv_down'] = path
                else:
                    raise Exception(f'Not recognizing file: {path}')
            else:
                raise Exception(f'Not recognizing file: {path}')

    def _add_local_cnv_file_path(self, file_path):
        self._files['local_cnv'] = file_path


class SveaFormerCTDFiles(SBECTDFiles):

    def _modify_and_save_cnv_file(self, save_directory=None, overwrite=False):
        cnv_column_info_directory = Path(Path(__file__).parent, 'cnv_column_info')
        cnv_obj = cnv.CNVfile(ctd_files=self, cnv_column_info_directory=cnv_column_info_directory)
        cnv_obj.modify()
        file_path = Path(save_directory, f'{self.stem}.cnv')
        cnv_obj.save_file(file_path=file_path, overwrite=overwrite)
        self._add_local_cnv_file_path(file_path)


class SveaFormerFinalSBECTDFiles(SveaFormerCTDFiles):
    """
    Former archive format used for CTD from Svea.
    This is the converted name pattern created by the old scripts before the implementation of the "Pre system" on Svea.
    """
    name = 'Former Svea CTD'
    pattern = 'SBE09_1387_\d{8}_\d{4}_77_10_\d{4}'
    pattern_example = 'SBE09_1387_20210413_1113_77_10_0278'

    @property
    def config_file_suffix(self):
        return '.XMLCON'

    def _get_proper_file_stem(self):
        stem = self._original_file_path.stem
        stem = stem[:25] + '77SE' + stem[30:]
        stem_parts = stem.split('_')
        stem_parts.insert(-1, '00')
        new_stem = '_'.join(stem_parts)
        return new_stem

class SveaSBECTDFiles(SBECTDFiles):
    """
    This is the file pattern that matches the one coming from the "Pre system" implemented on Svea.
    """
    name = 'Current Svea CTD'
    pattern = 'SBE09_1387_\d{8}_\d{4}_77SE_\d{2}_\d{4}'
    pattern_example = 'SBE09_1387_20210413_1113_77SE_01_0278'

    @property
    def config_file_suffix(self):
        return '.XMLCON'

    def _get_proper_file_stem(self):
        return self.file_path.stem

    def _modify_and_save_cnv_file(self, save_directory=None, overwrite=False):
        """ No modifications for now. Just copying the file. """
        target_path = Path(save_directory, f'{self.stem}.cnv')
        if target_path.exists() and not overwrite:
            raise FileExistsError(target_path)
        shutil.copy2(self._files['cnv_down'], target_path)
        self._add_local_cnv_file_path(target_path)


def get_ctd_files_object(file_path):
    files_object = [SveaFormerFinalSBECTDFiles(),
                    SveaSBECTDFiles()]
    for obj in files_object:
        if obj.is_valid(file_path):
            obj.set_file_path(file_path)
            return obj


def get_matching_files_in_directory(directory):
    directory = Path(directory)
    matching_files = {}
    for path in directory.iterdir():
        if path.stem in matching_files:
            continue
        obj = get_ctd_files_object(path)
        if not obj:
            continue
        matching_files[obj.file_path.name] = obj
    return matching_files


if __name__ == '__main__':

    f = r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210413_1113_77SE_00_0278.cnv'
    i = get_ctd_files_object(f)

    # f1 = Path(r'C:\mw\temp_ctd_pre_system_data_root\source/SBE09_1387_20210413_1422_77SE_01_0279.bl')
    # f2 = Path(r'C:\mw\temp_ctd_pre_system_data_root\source/SBE09_1387_20210413_1113_77_10_0278.bl')
    #
    # i1 = get_ctd_files_object(f1)
    # i2 = get_ctd_files_object(f2)
    # print(i1)
    # print(i2.proper_stem)
    #
    # files = get_matching_files_in_directory(r'C:\mw\temp\temp_ctd_processing\raw_files\2020')

    # si = SveaSBEInstrument()
    # si.set_file_path(r'C:\mw\temp_ctd_pre_system_data_root\source/SBE09_1387_20210413_1422_77SE_01_0279.bl')
    # print(si.get_proper_file_stem())
    #
    # sif = SveaFormerSBEInstrument()
    # sif.set_file_path(r'C:\mw\temp_ctd_pre_system_data_root\source/SBE09_1387_20210413_1113_77_10_0278.bl')
    # print(sif.get_proper_file_stem())
