import logging
import pathlib

import file_explorer
from file_explorer.seabird import paths

from ctd_processing import standard_format
from ctd_processing.processing.sbe_processing import SBEProcessing
from ctd_processing.processing.sbe_processing_paths import SBEProcessingPaths

logger = logging.getLogger(__name__)


class SBEProcessController:
    """
    This class is not intended to be used directly.
    It can be tricky to call all methods in the right order.
    Use a function below that suits your needs.
    """

    def __init__(self, target_root_directory, **kwargs):
        self.target_root_directory = target_root_directory
        self._overwrite = kwargs.get('overwrite', False)
        self.config_root_directory = None
        self.file_path = None
        self.pack = None

        self.sbe_paths = paths.SBEPaths()
        self.sbe_paths.set_local_root_directory(target_root_directory)
        self.sbe_processing_paths = SBEProcessingPaths(self.sbe_paths)
        self.sbe_processing = SBEProcessing(sbe_paths=self.sbe_paths,
                                            sbe_processing_paths=self.sbe_processing_paths)

    def set_config_root_directory(self, config_root_directory=None):
        if not config_root_directory:
            return
        self.sbe_paths.set_config_root_directory(config_root_directory)
        self.config_root_directory = config_root_directory

    def select_file(self, file_path=None):
        self.file_path = file_path
        self.pack = file_explorer.get_package_for_file(file_path)
        self.sbe_processing.select_file(self.pack['hex'])

    def confirm_file(self, file_path=None):
        if not file_path.samefile(self.file_path):
            raise Exception(f'Cant confirm file: {file_path}. Its not the one first selected!')
        self.sbe_processing.confirm_file(self.pack['hex'])

    def load_psa_config_zip(self):
        if not self.pack['zip']:
            raise Exception('No zip file with psa files found')
        self.sbe_processing_paths.load_psa_config_zip(self.pack['zip'])

    def load_psa_config_list(self, psa_paths=None):
        self.sbe_processing_paths.update_psa_paths(psa_paths or [])

    def reload_package(self, exclude_directory=None):
        if not self.pack:
            return
        self.pack = file_explorer.get_package_for_key(self.pack.key,
                                                      directory=self.sbe_paths.get_local_directory('root'),
                                                      exclude_directory=exclude_directory)

    def set_options(self, **kwargs):
        self.sbe_processing_paths.platform = kwargs.get('platform', 'sbe09')
        self.sbe_processing.set_surfacesoak(kwargs.get('surfacesoak', 'normal'))
        self.sbe_processing.set_tau_state(kwargs.get('tau', False))

    def process_file(self, **kwargs):
        self.pack = self.sbe_processing.run_process(overwrite=kwargs.get('overwrite', self._overwrite))

    def create_zip_with_psa_files(self):
        self.sbe_processing.create_zip_with_psa_files()

    def create_sensorinfo_file(self):
        if not self.config_root_directory:
            raise Exception('No Instrument.xlsx file found needed to create sensor info file')
        self.sbe_processing.create_sensorinfo_file()

    def create_standard_format(self, **kwargs):
        path = self.pack.get_file_path(suffix='.cnv', prefix=None)
        obj = standard_format.CreateStandardFormat(paths_object=self.sbe_paths)
        obj.create_files_from_cnv([path], overwrite=kwargs.get('overwrite', self._overwrite))


def process_sbe_file(path,
                     target_root_directory=None,
                     config_root_directory=None,
                     platform='sbe09',
                     surfacesoak='normal',
                     tau=False,
                     overwrite=False,
                     psa_paths=None):
    """
    Process seabird file using default psa files.
    Option to override psa files in psa_files
    """
    path = pathlib.Path(path)
    cont = SBEProcessController(target_root_directory=target_root_directory, overwrite=overwrite)
    cont.set_config_root_directory(config_root_directory)
    cont.select_file(path)
    cont.confirm_file(path)
    cont.load_psa_config_list(psa_paths)
    cont.set_options(tau=tau, platform=platform, surfacesoak=surfacesoak)
    cont.process_file()
    cont.create_zip_with_psa_files()
    cont.create_sensorinfo_file()
    cont.create_standard_format()


def reprocess_sbe_file(path,
                       target_root_directory=None,
                       config_root_directory=None,
                       surfacesoak='normal',
                       tau=False,
                       overwrite=False,
                       psa_paths=None):
    """
    Reprocess seabird file using psa files stored together with raw files.
    Option to override psa files in psa_files
    """
    path = pathlib.Path(path)
    cont = SBEProcessController(target_root_directory=target_root_directory, overwrite=overwrite)
    cont.set_config_root_directory(config_root_directory)
    cont.set_options(tau=tau, surfacesoak=surfacesoak)
    cont.select_file(path)
    cont.confirm_file(path)
    cont.load_psa_config_zip()
    cont.load_psa_config_list(psa_paths)
    cont.process_file()
    cont.create_zip_with_psa_files()
    cont.create_sensorinfo_file()
    cont.create_standard_format()


