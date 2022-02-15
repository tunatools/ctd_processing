import pathlib
import shutil

from ctd_processing import psa
from ctd_processing import ctd_files
from ctd_processing import sensor_info

from ctd_processing.processing.sbe_setup_file import SBESetupFile
from ctd_processing.processing.sbe_batch_file import SBEBatchFile


class SBEProcessing:
    """
    Config file paths are hard coded based on the root catalogue. Consider putting this info in config file (yaml, json)
    """

    def __init__(self, sbe_paths=None, sbe_processing_paths=None):
        self._paths = sbe_paths
        self._processing_paths = sbe_processing_paths

        self._file_path = None
        self._confirmed = False
        self._overwrite = False
        self._ctd_files = None

    @property
    def platform(self):
        return self._processing_paths.platform

    @platform.setter
    def platform(self, name):
        # Setting the platform. This is used for prioritising setup files in a specific folder in ctd_config\SBE\processing_psa
        if not name:
            return
        if name.lower() not in self._processing_paths.platforms:
            raise Exception(f'Invalid platform name: {name}')
        self._processing_paths.platform = name

    @property
    def year(self):
        if not self._ctd_files:
            return None
        return self._ctd_files.year

    def get_platform_options(self):
        return self._processing_paths.platforms

    def get_surfacesoak_options(self):
        options = {}
        print('self._processing_paths', self._processing_paths)
        for path in self._processing_paths.loopedit_paths:
            name = path.name.lower()
            obj = psa.LoopeditPSAfile(path)
            depth_str = str(int(float(obj.depth)))
            if 'deep' in name:
                options[f'Deep {depth_str} m'] = path
            elif 'shallow' in name:
                options[f'Shallow {depth_str} m'] = path
            else:
                options[f'Normal {depth_str} m'] = path
        return options

    def set_platform(self, platform):
        self._processing_paths.platform = platform

    def set_surfacesoak(self, name):
        """ Sets surfacesoak in setup file. Name must match keys in coming from self.get_surfacesoak_options """
        name = name.lower()
        options = self.get_surfacesoak_options()
        for key, path in options.items():
            if name in key.lower():
                self._processing_paths.set_loopedit(path)
                return (key, path)
        else:
            raise Exception('Invalid surfacesoak option')

    def _get_derive_psa_obj(self):
        # file_paths = self.get_file_paths()
        return psa.DerivePSAfile(self._processing_paths('psa_derive'))

    def set_tau_state(self, state):
        self._get_derive_psa_obj().set_tau_correction(bool(bool))

    def select_file(self, file_path):
        """ Kontrollen för att skriva över bör göras mot raw-mappen istället för mot tempmappen. """
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        self._file_path = path
        self._ctd_files = ctd_files.get_ctd_files_object(path)
        self._paths.set_year(self.year)
        # self._paths.set_raw_file_path(self._ctd_files.file_path)
        # self._paths.set_config_suffix(self._ctd_files.config_file_suffix)
        self._confirmed = False

    def confirm_file(self, file_path):
        if not self._file_path:
            raise Exception('No file selected')
        path = pathlib.Path(file_path)
        if not path.samefile(self._file_path):
            raise PermissionError('Confirmed file is not the same as the selected!')
        # Copying files and load instrument files object
        new_path = self._copy_all_files_with_same_file_stem_to_working_dir(path)
        self._ctd_files = ctd_files.get_ctd_files_object(new_path)
        self._ctd_files.rename_files(overwrite=True)
        self._processing_paths.set_raw_file_path(self._ctd_files.file_path)
        self._processing_paths.set_config_suffix(self._ctd_files.config_file_suffix)
        self._setup_file = SBESetupFile(paths=self._paths,
                                        processing_paths=self._processing_paths,
                                        instrument_files=self._ctd_files)
        self._batch_file = SBEBatchFile(paths=self._paths,
                                        processing_paths=self._processing_paths)
        self._confirmed = True
        return self._ctd_files.file_path

    def _copy_raw_files_to_local(self):
        target_directory = self._paths.get_local_directory('raw', create=True)
        file_paths = [value for key, value in self._ctd_files.all_files.items() if
                      key.lower() in self._ctd_files.raw_files_extensions]
        for file_path in file_paths:
            self._copy_file(file_path, target_directory, overwrite=self._overwrite)

    def _copy_cnv_files_to_local(self):
        """ Copies cnv-up file to local directory """
        target_directory = self._paths.get_local_directory('cnv_up', create=True)
        return self._copy_file(self._ctd_files('cnv_up'), target_directory, overwrite=self._overwrite)

    def _copy_plot_files_to_local(self):
        target_directory = self._paths.get_local_directory('plot', create=True)
        for file_path in self._ctd_files.plot_files:
            self._copy_file(file_path, target_directory, overwrite=self._overwrite)

    def _copy_processed_files_to_local(self):
        print('-' * 50)
        for key, value in self._ctd_files.all_files.items():
            print(key, value)
        self._copy_raw_files_to_local()
        self._copy_cnv_files_to_local()
        self._copy_plot_files_to_local()

    def _copy_all_files_with_same_file_stem_to_working_dir(self, file_path):
        target_directory = self._paths('working_dir', create=True)
        stem = file_path.stem
        return_path = None
        for path in file_path.parent.iterdir():
            if path.stem == stem:
                return_path = self._copy_file(path, target_directory, overwrite=True)
        return return_path

    def _copy_file(self, source_file_path, target_directory, overwrite=False):
        target_file_path = pathlib.Path(target_directory, source_file_path.name)
        if target_file_path.exists() and not overwrite:
            raise FileExistsError(target_file_path)
        shutil.copy2(source_file_path, target_file_path)
        return target_file_path

    def get_file_names_in_server_directory(self, subfolder=None):
        directory = self._paths.get_server_directory(subfolder)
        return [path.name for path in directory.iterdir()]

    # def get_local_directory(self, subfolder=None, create=False):
    #     key = f'local_dir_{subfolder}'
    #     return self._paths(key, create=create)
    #
    # def get_server_directory(self, subfolder=None, create=False):
    #     key = f'server_dir_{subfolder}'
    #     return self._paths(key, create=create)

    def run_process(self, overwrite=False):
        if not self._confirmed:
            raise Exception('No file confirmed!')
        self._overwrite = bool(overwrite)
        self._setup_file.create_file()
        self._batch_file.create_file()
        self._batch_file.run_file()
        print('='*50)
        for key, value in self._ctd_files.all_files.items():
            print(key, value)
        self._ctd_files.add_processed_file_paths()
        self._ctd_files.modify_and_save_cnv_file(save_directory=self._paths.get_local_directory('cnv', create=True),
                                                 overwrite=self._overwrite)
        self._copy_processed_files_to_local()

    def create_sensorinfo_file(self):
        if not self._ctd_files('local_cnv'):
            return
        sensor_info_obj = sensor_info.get_sensor_info_object(self._paths('instrumentinfo_file'))
        sensor_info_obj.create_file_from_cnv_file(self._ctd_files('local_cnv'))