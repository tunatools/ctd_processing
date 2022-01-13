from abc import abstractmethod

from ctd_processing.ctd_files.parent_abc_class import CTDFiles
from ctd_processing.ctd_files.seabird import BlFile
from ctd_processing.ctd_files.seabird import HdrFile
from ctd_processing.cnv import CNVfileInfo


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
            obj = CNVfileInfo(self._files['.cnv'])
        return obj.station

    @property
    def lat(self):
        if not self._files.get('.cnv'):
            return None
        return CNVfileInfo(self._files['.cnv']).lat

    @property
    def lon(self):
        if not self._files.get('.cnv'):
            return None
        return CNVfileInfo(self._files['.cnv']).lon

    @property
    def time(self):
        if self._files.get('.hdr'):
            obj = HdrFile(self._files['.hdr'])
        else:
            obj = CNVfileInfo(self._files['.cnv'])
        return obj.time

    @property
    def year(self):
        return self.time.year

    @property
    def number_of_bottles(self):
        obj = BlFile(self._files['.bl'])
        return obj.number_of_bottles

    @property
    def file_path(self):
        path = self._files.get('.hex')
        if not path:
            return self._files.get('.cnv')
        return path

    def add_processed_file_paths(self):
        """ Adds files created by seasave. Saves filepaths with same file stem"""
        self._plot_files = []
        stem = self.stem.upper()
        for path in self.parent.iterdir():
            suffix = path.suffix.lower()
            if stem not in str(path).upper():
                continue
            if path in self._files.values():
                continue
            if suffix == '.jpg':
                self._plot_files.append(path)
            elif suffix in ['.bl', '.btl', '.ros']:
                self._files[suffix] = path
            elif suffix == '.cnv':
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