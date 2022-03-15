import os
import pathlib
import shutil

import file_explorer
from file_explorer import psa
from file_explorer import seabird

from ctd_processing import modify_cnv
from ctd_processing import sensor_info
from ctd_processing.processing.sbe_batch_file import SBEBatchFile
from ctd_processing.processing.sbe_setup_file import SBESetupFile


class SBEProcessing:

    def __init__(self, sbe_paths=None, sbe_processing_paths=None):
        self._paths = sbe_paths
        self._processing_paths = sbe_processing_paths

        self._file_path = None
        self._confirmed = False
        self._overwrite = False
        self._package = None

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
        if not self._package:
            return None
        return self._package('year')

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
        return psa.DerivePSAfile(self._processing_paths('psa_derive'))

    def set_tau_state(self, state):
        self._get_derive_psa_obj().set_tau_correction(bool(bool))

    def select_file(self, file_path):
        """ Kontrollen för att skriva över bör göras mot raw-mappen istället för mot tempmappen. """
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        self._file_path = path
        self._package = file_explorer.get_package_for_file(path)
        self._paths.set_year(self.year)
        self._confirmed = False

    def confirm_file(self, file_path):
        if not self._file_path:
            raise Exception('No file selected')
        path = pathlib.Path(file_path)
        if not path.samefile(self._file_path):
            raise PermissionError('Confirmed file is not the same as the selected!')
        # Copying files and load instrument files object
        new_path = self._copy_all_files_with_same_file_stem_to_working_dir(path)
        self._package = file_explorer.get_package_for_file(new_path)
        self._package = file_explorer.rename_package(self._package, overwrite=True)
        self._processing_paths.set_raw_file_path(self._package['hex'])
        self._processing_paths.set_config_suffix(self._package('config_file_suffix'))
        self._setup_file = SBESetupFile(paths=self._paths,
                                        processing_paths=self._processing_paths,
                                        instrument_files=self._package)
        self._batch_file = SBEBatchFile(paths=self._paths,
                                        processing_paths=self._processing_paths)
        self._confirmed = True
        return self._package['hex']

    def _copy_raw_files_to_local(self):
        target_directory = self._paths.get_local_directory('raw', create=True)
        for file in self._package.get_raw_files():
            self._copy_file(file, target_directory, overwrite=self._overwrite)

    def _copy_cnv_files_to_local(self):
        """ Copies cnv-up file to local directory """
        target_directory = self._paths.get_local_directory('cnv_up', create=True)
        return self._copy_file(self._package.get_file(suffix='.cnv', prefix='u'), target_directory, overwrite=self._overwrite)

    def _copy_plot_files_to_local(self):
        target_directory = self._paths.get_local_directory('plot', create=True)
        for file in self._package.get_plot_files():
            self._copy_file(file, target_directory, overwrite=self._overwrite)

    def _copy_processed_files_to_local(self):
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

    def _copy_file(self, source_file, target_directory, overwrite=False):
        if isinstance(source_file, file_explorer.file.InstrumentFile):
            source_file_path = source_file.path
            target_file_path = source_file.get_proper_path(target_directory)
        else:  # pathlib.Path
            source_file_path = source_file
            target_file_path = pathlib.Path(target_directory, source_file.name)

        if target_file_path.exists():
            if not overwrite:
                raise FileExistsError(target_file_path)
            else:
                os.remove(target_file_path)
        shutil.copy2(source_file_path, target_file_path)
        return target_file_path

    def get_file_names_in_server_directory(self, subfolder=None):
        directory = self._paths.get_server_directory(subfolder)
        return [path.name for path in directory.iterdir()]

    def run_process(self, overwrite=False):
        if not self._confirmed:
            raise Exception('No file confirmed!')
        self._overwrite = bool(overwrite)
        self._setup_file.create_file()
        self._batch_file.create_file()
        self._batch_file.run_file()

        file_explorer.update_package_with_files_in_directory(self._package, self._paths.get_local_directory('temp'))
        modify_cnv.modify_cnv_down_file(self._package,
                                     directory=self._paths.get_local_directory('cnv', create=True),
                                     overwrite=self._overwrite)
        file_explorer.update_package_with_files_in_directory(self._package, self._paths.get_local_directory('cnv'), replace=True)
        self._copy_processed_files_to_local()
        self._package = file_explorer.get_package_for_file(self._package, directory=self._paths.get_local_directory('root'),
                                                           exclude_directory='temp')

    def create_sensorinfo_file(self):
        file = self._package.get_file(suffix='.cnv', prefix=None)
        sensor_info_obj = sensor_info.get_sensor_info_object(self._paths('instrumentinfo_file'))
        sensor_info_obj.create_file_from_cnv_file(file.path)