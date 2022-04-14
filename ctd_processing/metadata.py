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


class PackageMetadata:
    def __init__(self, package, **kwargs):
        self._pack = package
        self._cnv = self._pack.get_file(prefix=None, suffix='.cnv')
        self._metadata = {}
        self._metadata_columns = get_metadata_columns()
        self._save_metadata(**kwargs)

    def _save_metadata(self, **kwargs):
        self._metadata = {}
        for col in self._metadata_columns:
            if col == 'POSYS':
                value = 'GPS'
            elif col == 'SMTYP':
                value = 'CTD'
            else:
                value = self._cnv(MAPPING.get(col, col)) or kwargs.get(col) or ''
            self._metadata[col] = value

    def get_metadata(self):
        return self._metadata.copy()


class CreateMetadataFile:

    def __init__(self, package, **kwargs):
        self._pack = package
        self._stem = None
        self._save_path = None
        self._data = None

        self._save_info(**kwargs)

    def __str__(self):
        return f'CreateMetadataFile'

    def _save_info(self, **kwargs):
        metarow = PackageMetadata(self._pack, **kwargs)
        self._data = metarow.get_metadata()

    def write_to_file(self):
        file_path = self._pack.get_file_path(prefix=None, suffix='.cnv')
        if not file_path:
            file_path = self._pack.get_file_path(suffix='.txt')
        if not file_path:
            raise FileNotFoundError(f'No cnv or standard format file found in package: {self._pack.key}')

        path = pathlib.Path(file_path.parent, f'{file_path.stem}.metadata')
        columns = get_metadata_columns()
        lines = []
        lines.append('\t'.join(columns))
        lines.append('\t'.join([self._data.get(key, '') for key in columns]))
        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))
        return path


class CreateMetadataSummaryFile:

    def __init__(self, directory):
        self._directory = pathlib.Path(directory)
        self._paths = [path for path in self._directory.iterdir() if path.suffix == '.metadata']
        self._metadata = []
        self._save_info()

    def _save_info(self):
        for path in self._paths:
            header = None
            with open(path) as fid:
                for line in fid:
                    if not line.strip():
                        continue
                    split_line = [item.strip() for item in line.split('\t')]
                    if not header:
                        header = split_line
                        continue
                    meta = dict(zip(header, split_line))
                    self._metadata.append(meta)

    def write_summary_to_file(self, directory=None):
        if not directory:
            directory = self._directory
        path = pathlib.Path(directory, 'metadata.txt')
        columns = get_metadata_columns()
        lines = []
        lines.append('\t'.join(columns))
        for meta in self._metadata:
            lines.append('\t'.join(meta))
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
    mdf = CreateMetadataFile(r'C:\mw\temp_ctd_pre_system_data_root\cnv')
    mdf.write_to_file()

    hfi = modify_cnv.get_header_form_information(r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210413_1113_77SE_00_0278.cnv')
