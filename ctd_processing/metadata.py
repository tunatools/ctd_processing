import pathlib

from ctd_processing import cnv
from ctd_processing import ctd_files


class MetadataRow:
    def __init__(self):
        self._path = None
        self._metadata = {}
        self._metadata_columns = get_metadata_columns()

    def get_metadata_row_from_cnv_file(self, path):
        self._path = pathlib.Path(path)
        self._save_metadata()
        return self.get_info()

    def _save_metadata(self):
        header_form_info = cnv.get_header_form_information(self._path)
        ctd_info = ctd_files.get_ctd_files_object(self._path)
        self._metadata = {}
        for col in self._metadata_columns:
            value = header_form_info.get(col, '')
            if col == 'MYEAR':
                value = str(ctd_info.year)
            elif col == 'SDATE':
                value = ctd_info.time.strftime('%Y-%m-%d')
            elif col == 'STIME':
                value = ctd_info.time.strftime('%H:%S')
            elif col == 'SHIPC':
                value = header_form_info.get('Cruise').split('-')[0]
            elif col == 'CRUISE_NO':
                value = header_form_info.get('Cruise')
            elif col == 'SERNO':
                value = ctd_info.serno
            elif col == 'STATN':
                value = ctd_info.station
            elif col == 'LATIT':
                value = ctd_info.lat
            elif col == 'LONGI':
                value = ctd_info.lon
            elif col == 'POSYS':
                value = 'GPS'
            elif col == 'ADS_SMP':
                value = header_form_info.get('Additional Sampling')
            elif col == 'FILE_NAME':
                value = self._path.name
            elif col == 'INSTRUMENT_SERIE':
                value = ctd_info.instrument_number
            self._metadata[col] = value

    def get_info(self):
        return self._metadata.copy()


class MetadataFile:

    def __init__(self, directory):
        self._directory = pathlib.Path(directory)
        self._paths = [path for path in self._directory.iterdir() if path.suffix == '.cnv']
        self._stem = None
        self._save_path = None
        self._data = None

        self._save_info()

    def __str__(self):
        return f'MetadataFile'

    def _save_info(self):
        self._data = {}
        for path in self._paths:
            metarow = MetadataRow()
            self._data[path] = metarow.get_metadata_row_from_cnv_file(path)

    def write_to_file(self):
        path = pathlib.Path(self._directory, 'metadata.txt')
        columns = get_metadata_columns()
        lines = []
        lines.append('\t'.join(columns))
        for info in self._data.values():
            lines.append('\t'.join([info.get(key, '') for key in columns]))
        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))


def get_metadata_columns():
    path = pathlib.Path(pathlib.Path(__file__).parent, 'resources', 'metadata_columns.txt')
    columns = []
    with open(path) as fid:
        for line in fid:
            sline = line.strip()
            if not sline:
                continue
            columns.append(sline)
    return columns


if __name__ == '__main__':
    mdf = MetadataFile(r'C:\mw\temp_ctd_pre_system_data_root\cnv')
    mdf.write_to_file()

    hfi = cnv.get_header_form_information(r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210413_1113_77SE_00_0278.cnv')
