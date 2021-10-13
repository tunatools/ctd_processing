import pathlib
import datetime
import codecs


class old_CnvFile:
    def __init__(self, file_path):
        self._path = pathlib.Path(file_path)

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