from pathlib import Path
import datetime
import os


class SBEPaths:
    def __init__(self):
        self._paths = {}
        self._year = None
        self._sub_dir_list_local = ['source', 'raw', 'cnv', 'nsf', 'cnv_up', 'plot', 'temp']
        self._sub_dir_list_server = ['raw', 'cnv', 'nsf', 'cnv_up']

    def __call__(self, key, create=False, default=None, **kwargs):
        path = self._paths.get(key)
        if not path:
            if default is not None:
                return default
            return False
        if create and not path.exists():
            os.makedirs(str(path))
        return path

    @property
    def year(self):
        return self._year

    @property
    def local_sub_directories(self):
        return self._sub_dir_list_local

    @property
    def server_sub_directories(self):
        return self._sub_dir_list_server

    def _local_key(self, key=None):
        if key not in self.local_sub_directories + ['root']:
            raise Exception(f'Not a valid sub directory: {key}')
        return f'local_dir_{key}'

    def _server_key(self, key=None):
        if key not in self.server_sub_directories + ['root']:
            raise Exception(f'Not a valid sub directory: {key}')
        return f'server_dir_{key}'

    def get_local_directory(self, key, create=False, default=None):
        return self(self._local_key(key), create=create, default=default)

    def get_server_directory(self, key, year=None, create=False, default=None):
        # if key not in self.server_sub_directories + ['root']:
        #     return False
        if year:
            return self._get_server_directory_for_year(key, year, create=create)
        return self(self._server_key(key), create=create, default=default)

    def create_local_paths(self):
        for key in self._sub_dir_list:
            self.get_local_directory(key, create=True)

    def create_server_paths(self, year=None):
        if not year:
            year = datetime.datetime.now().year
        for key in self._sub_dir_list:
            self.get_server_directory(key, year=year, create=True)

    def _get_server_directory_for_year(self, key, year, create=False):
        if key not in self._sub_dir_list_server:
            raise Exception(f'Invalid directory: {key}')
        path = Path(self._paths['server_dir_root'], str(year), key)
        if create and not path.exists():
            os.makedirs(path)
        return path

    def set_config_root_directory(self, path):
        self._paths['config_dir'] = Path(path)
        # self._paths['instrumentinfo_file'] = Path(self._paths['config_dir'], 'instrumentinfo.xlsx')
        self._paths['instrumentinfo_file'] = Path(self._paths['config_dir'], 'Instruments.xlsx')

    def set_local_root_directory(self, directory):
        root_directory = Path(directory)
        if root_directory.name == 'data':
            root_directory = root_directory.parent
        self._paths['local_dir_root'] = root_directory
        self._paths['working_dir'] = Path(self._paths['local_dir_root'], 'temp')
        self._paths['local_dir_temp'] = self._paths['working_dir'] 
        self._paths['local_dir_source'] = Path(self._paths['local_dir_root'], 'source')
        self._paths['local_dir_raw'] = Path(self._paths['local_dir_root'], 'raw')
        self._paths['local_dir_cnv'] = Path(self._paths['local_dir_root'], 'cnv')
        self._paths['local_dir_cnv_up'] = Path(self._paths['local_dir_root'], 'cnv', 'up_cast')
        self._paths['local_dir_nsf'] = Path(self._paths['local_dir_root'], 'data')
        self._paths['local_dir_plot'] = Path(self._paths['local_dir_root'], 'plots')

    def set_server_root_directory(self, directory):
        print('set_server_root_directory', directory)
        self._paths['server_dir_root'] = Path(directory)
        self.set_year()

    def set_year(self, year=None):
        """ Year is neaded to set sub directories for the different filtypes """
        if year:
            self._year = str(year)
        if self._year and self._paths.get('server_dir_root'):
            self._paths['server_dir_raw'] = Path(self._paths['server_dir_root'], self._year, 'raw')
            self._paths['server_dir_cnv'] = Path(self._paths['server_dir_root'], self._year, 'cnv')
            self._paths['server_dir_nsf'] = Path(self._paths['server_dir_root'], self._year, 'data')
            self._paths['server_dir_cnv_up'] = Path(self._paths['server_dir_root'], self._year, 'cnv_up')