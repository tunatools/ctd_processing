import pathlib

from ctd_processing import modify_cnv
import file_explorer


MAPPING = {'MYEAR': 'year',
           'SDATE': 'date',
           'STIME': 'time',
           'SHIPC': 'ship',
           'CRUISE_NO': 'cruise',
           'SERNO': 'serno',
           'STATN': 'station',
           'LATIT': 'lat',
           'LONGI': 'lon',
           'FILE_NAME': 'name',
           'INSTRUMENT_SERIE': 'instrument_number'}


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
        file = file_explorer.get_file_object_for_path(self._path)
        self._metadata = {}
        for col in self._metadata_columns:
            if col == 'POSYS':
                value = 'GPS'
            elif col == 'SMTYP':
                value = 'CTD'
            else:
                print(col, MAPPING.get(col, col), file(MAPPING.get(col, col)))
                value = file(MAPPING.get(col, col)) or ''
            self._metadata[col] = value

    def get_info(self):
        return self._metadata.copy()


class MetadataFile:

    def __init__(self, directory=None, file_list=None):
        if directory:
            self._directory = pathlib.Path(directory)
            self._paths = [path for path in self._directory.iterdir() if path.suffix == '.cnv']
        elif file_list:
            self._paths = []
            for file_path in file_list:
                path = pathlib.Path(file_path)
                if path.suffix != '.cnv':
                    continue
                self._paths.append(path)
        else:
            raise Exception('No info given to class MetadataFile')
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

    def write_to_file(self, output_dir=None):
        if not output_dir:
            output_dir = self._directory
        path = pathlib.Path(output_dir, 'metadata.txt')
        columns = get_metadata_columns()
        lines = []
        lines.append('\t'.join(columns))
        for info in self._data.values():
            lines.append('\t'.join([info.get(key, '') for key in columns]))
        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))
        return path


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

    hfi = modify_cnv.get_header_form_information(r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210413_1113_77SE_00_0278.cnv')
