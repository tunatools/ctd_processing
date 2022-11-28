
from pathlib import Path
import shutil
import filecmp

from ctd_processing import exceptions

import logging


logger = logging.getLogger(__name__)

PREFIX_SUFFIX_SUBFOLDER_MAPPING = {
    (None, '.cnv'): 'cnv',
    (None, '.sensorinfo'): 'cnv',
    (None, '.metadata'): 'cnv',
    (None, '.deliverynote'): 'cnv',
    ('u', '.cnv'): 'cnv_up',
    (None, '.jpg'): 'plot',
    (None, '.bl'): 'raw',
    (None, '.btl'): 'raw',
    (None, '.hdr'): 'raw',
    (None, '.hex'): 'raw',
    (None, '.ros'): 'raw',
    (None, '.xmlcon'): 'raw',
    (None, '.con'): 'raw',
    (None, '.zip'): 'raw',
    (None, '.txt'): 'nsf',
}


class SBEFileHandler:
    def __init__(self, paths_object):
        self.paths = paths_object
        self.local_files = {}
        self.server_files = {}

    def select_file(self, path):
        """ This will load all files matching the file_paths file stem. Loading files in paths_object. """
        file_stem = Path(path).stem
        self.select_stem(file_stem)

    def select_stem(self, stem):
        if not stem.startswith('SBE'):
            raise exceptions.InvalidFileNameFormat('Not a valid file')
        year = stem.split('_')[2][:4]
        self.paths.set_year(year)
        self._load_files(stem)

    def select_pack(self, pack):
        self.paths.set_year(pack('year'))
        self._load_files(pack.pattern)

    def _load_files(self, file_stem):
        self._load_local_files(file_stem)
        self._load_server_files(file_stem)

    def _load_local_files(self, file_stem):
        self.local_files = {}
        for sub in self.paths.local_sub_directories:
            local_path = self.paths.get_local_directory(sub, create=True)
            if local_path:
                for path in local_path.iterdir():
                    if file_stem.lower() in path.stem.lower(): # this is to include upcast with prefix "u"
                    # if file_stem == path.stem:
                        obj = File(path)
                        self.local_files[(sub, obj.name)] = obj

    def _load_server_files(self, file_stem):
        self.server_files = {}
        for sub in self.paths.server_sub_directories:
            server_path = self.paths.get_server_directory(sub, create=True)
            if server_path:
                for path in server_path.iterdir():
                    if file_stem.lower() in path.stem.lower():  # this is to include upcast with prefix "u"
                        # if file_stem == path.stem:
                        obj = File(path)
                        self.server_files[(sub, obj.name)] = obj

    def _not_on_server(self):
        """ Returns a dict with the local files that are not on server """
        result = {}
        for key, path in self.local_files.items():
            sub, name = key
            if sub not in self.paths.server_sub_directories:
                continue
            if not self.server_files.get(key):
                result[key] = path
        return result

    def _not_updated_on_server(self):
        """ Returns a dict with local files that are not updated on server """
        result = {}
        for key, server in self.server_files.items():
            local = self.local_files.get(key)
            if not local:
                continue
            if local == server:
                continue
            result[key] = local
        return result

    def not_on_server(self):
        return bool(self._not_on_server())

    def not_updated_on_server(self):
        return bool(self._not_updated_on_server())

    def copy_files_to_server(self, update=False):
        print('_not_on_server', self._not_on_server())
        for key, path in self._not_on_server().items():
            sub, name = key
            server_directory = self.paths.get_server_directory(sub)
            print('server_directory', server_directory)
            if not server_directory:
                continue
            target_path = Path(server_directory, path.name)
            shutil.copy2(path(), target_path)
        if update:
            for key, path in self._not_updated_on_server().items():
                sub, name = key
                server_directory =self.paths.get_server_directory(sub)
                if not server_directory:
                    continue
                target_path = Path(server_directory, path.name)
                shutil.copy2(path(), target_path)

    def get_local_file_path(self, subdir=None, suffix=None):
        paths = []
        for key, file in self.local_files.items():
            if key[0] == subdir:
                if suffix and file.suffix == suffix:
                    return file.path
                paths.append(file.path)
        if len(paths) == 1:
            return paths[0]
        return paths


class File:
    def __init__(self, file_path):
        self.path = Path(file_path)

    def __str__(self):
        return str(self.path)

    def __call__(self):
        return self.path

    def __eq__(self, other):
        if not other:
            return None
        return filecmp.cmp(self.path, other(), shallow=False)

    @property
    def name(self):
        return self.path.name

    @property
    def suffix(self):
        return self.path.suffix


def copy_package_to_local(pack, path_object, overwrite=False, rename=False):
    """
    Copy all files in package to local. Returning new package.
    """
    import file_explorer
    path_object.set_year(pack('year'))
    for file in pack.get_files():
        path = file.path
        key1 = (file.prefix, file.suffix)
        key2 = (None, file.suffix)
        key = PREFIX_SUFFIX_SUBFOLDER_MAPPING.get(key1) or PREFIX_SUFFIX_SUBFOLDER_MAPPING.get(key2)
        if not key:
            logger.info(f'Can not find destination subfolder for file: {path}')
            continue
        target_dir = path_object.get_local_directory(key, year=pack('year'), create=True)
        if rename:
            target_path = Path(target_dir, file.get_proper_name())
        else:
            target_path = Path(target_dir, path.name)
        if target_path.exists() and not overwrite:
            raise FileExistsError(target_path)
        print(target_path)
        shutil.copy2(path, target_path)

    return file_explorer.get_package_for_key(pack.key, path_object.get_local_directory('root'), exclude_directory='temp')


def copy_package_to_temp(pack, path_object, overwrite=False, rename=False):
    import file_explorer
    path_object.set_year(pack('year'))
    return file_explorer.copy_package_to_directory(pack,
                                                   path_object.get_local_directory('temp'),
                                                   overwrite=overwrite,
                                                   rename=rename)
