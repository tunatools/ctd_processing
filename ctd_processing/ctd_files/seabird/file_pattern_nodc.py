import pathlib
import shutil

from ctd_processing.ctd_files.seabird import ModifyCTDfiles


class NODCSBECTDFiles(ModifyCTDfiles):
    """
    This is the file pattern that matches the one coming from the "Pre system" implemented on Svea.
    """
    name = 'NODC SBE CTD file '
    # pattern = 'SBE\d{2}_\d{4}_\d{8}_\d{4}_\d{4}_\d{2}_\d{4}'
    pattern_example = 'SBE09_1387_20210413_1113_77SE_01_0278'
    pattern = '^{}_{}_{}_{}_{}_{}_{}$'.format(
        '(?P<platform>SBE\d{2})',
        '(?P<instrument>\d{4})',
        '(?P<date>\d{8})',
        '(?P<time>\d{4})',
        '(?P<ship>\d{2}\w{2})',
        '(?P<cruise>\d{2})',
        '(?P<serno>\d{4})',
    )

    @property
    def instrument_number(self):
        # Information not in file name in former raw files. Should be in child.
        return self._file_name_info['instrument']
        # return self.stem.split('_')[1]

    @property
    def shipcode(self):
        return self._file_name_info['ship']
        # return self.stem.split('_')[4]

    @property
    def serno(self):
        return self._file_name_info['serno']
        # return self.stem.split('_')[-1]

    @property
    def config_file_suffix(self):
        return '.XMLCON'

    def _get_proper_file_stem(self):
        return self.file_path.stem

    # def _modify_and_save_cnv_file(self, save_directory=None, overwrite=False):
    #     """ No modifications for now. Just copying the file. """
    #     target_path = pathlib.Path(save_directory, f'{self.stem}.cnv')
    #     if target_path.exists() and not overwrite:
    #         raise FileExistsError(target_path)
    #     shutil.copy2(self._files['cnv_down'], target_path)
    #     self._add_local_cnv_file_path(target_path)
