import datetime
import codecs


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