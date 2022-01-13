from abc import ABC, abstractmethod
import pathlib
import re
import os


class CTDFiles(ABC):
    _original_file_path = None
    _files = {}
    _plot_files = []
    _file_name_info = {}
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
    def shipcode(self):
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
        file_path = pathlib.Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        if not self._check_file_stem(file_path):
            raise Exception(f'File "{file_path}" does not match stem pattern "{self.pattern}"')
        self._original_file_path = file_path
        self._save_file_paths(file_path)

    def rename_files(self, overwrite=False):
        """ Rename the files so they get the proper file stem """
        new_files = {}
        print('#######')
        print(self._files)
        for key, path in self._files.items():
            new_path = self._rename_file(path, overwrite=overwrite)
            new_files[key] = new_path
        self._files = new_files

    def _rename_file(self, path, overwrite=False):
        """ Rename a single file with the proper file stem """
        new_path = pathlib.Path(path.parent, f'{self.proper_stem}{path.suffix}')
        if str(new_path) == str(path):
            return new_path
        if new_path.exists():
            if not overwrite:
                raise FileExistsError(new_path)
            os.remove(new_path)
        path.rename(new_path)
        return new_path

    def _check_file_stem(self, file_path):
        name_re = re.compile(self.pattern)
        name_match = name_re.search(file_path.stem)

        if not name_match:
            return False
        self._file_name_info = name_match.groupdict()
        return True

    def _save_file_paths(self, file_path):
        self._files = {}
        for path in file_path.parent.iterdir():
            if path.stem.lower() == file_path.stem.lower():
                self._files[path.suffix.lower()] = path

    def is_valid(self, file_path):
        file_path = pathlib.Path(file_path)
        if not file_path.exists():
            return False
        return self._check_file_stem(file_path)
