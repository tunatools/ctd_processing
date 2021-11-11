
from pathlib import Path
import shutil
import filecmp


class SBEFileHandler:
    def __init__(self, paths_object):
        self.paths = paths_object
        self.local_files = {}
        self.server_files = {}

    def select_file(self, path):
        """ This will load all files matching the file_paths file stem. Loading files in paths_object. """
        file_stem = Path(path).stem
        if not file_stem.startswith('SBE'):
            raise Exception('Not a valid file')
        year = file_stem.split('_')[2][:4]
        self.paths.set_year(year)
        self._load_files(file_stem)

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

    def get_local_file_path(self, suffix):
        paths = []
        for key, file in self.local_files.items():
            if key[0] in suffix:
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


if __name__ == '__main__':
    sbe_paths = SBEPaths()
    sbe_paths.set_local_root_directory(r'C:\mw\temp_ctd_pre_system_data_root')
    sbe_paths.set_server_root_directory(r'C:\mw\temp_ctd_pre_system_data_root_server')
    sbe_paths.create_server_paths()

    f = SBEFileHandler(paths_object=sbe_paths)
    f.select_file(file_stem='SBE09_1387_20210414_0058_77SE_00_0284')
    f.copy_files_to_server()