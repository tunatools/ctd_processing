from ctd_processing.ctd_files.seabird import ModifyCTDfiles


class OldSBECTDFiles(ModifyCTDfiles):
    """
    Former archive format used for CTD from Svea.
    This is the converted name pattern created by the old scripts before the implementation of the "Pre system" on Svea.
    """
    name = 'Former CTD SBE file pattern'
    # pattern = 'SBE09_\d{4}_\d{8}_\d{4}_\d{4}_\d{4}_\d{4}'
    pattern_example = 'SBE09_1387_20210413_1113_77_10_0278'
    pattern = '^{}_{}_{}_{}_{}_{}$'.format(
            '(?P<platform>SBE\d{2})',
            '(?P<instrument>\d{4})',
            '(?P<date>\d{8})',
            '(?P<time>\d{4})',
            '(?P<ship>(\d{2}_\d{2}))',
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
        stem = self._original_file_path.stem
        stem = stem[:25] + '77SE' + stem[30:]
        stem_parts = stem.split('_')
        stem_parts.insert(-1, '00')
        new_stem = '_'.join(stem_parts)
        return new_stem