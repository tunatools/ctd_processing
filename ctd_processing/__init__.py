import logging

import file_explorer
from file_explorer.seabird import paths

from ctd_processing.processing.sbe_processing import SBEProcessing
from ctd_processing.processing.sbe_processing_paths import SBEProcessingPaths

logger = logging.getLogger(__name__)


def reprocess_sbe_file(path,
                       target_root_directory=None,
                       config_root_directory=None,
                       tau=False,
                       overwrite=False):
    if target_root_directory is None:
        raise NotADirectoryError('No target root directory provided')
    sbe_paths = paths.SBEPaths()
    sbe_processing_paths = SBEProcessingPaths(sbe_paths)

    sbe_processing = SBEProcessing(sbe_paths=sbe_paths,
                                   sbe_processing_paths=sbe_processing_paths)

    sbe_paths.set_local_root_directory(target_root_directory)

    pack = file_explorer.get_package_for_file(path)

    sbe_processing_paths.load_psa_config_zip(pack['zip'])

    sbe_processing.select_file(pack['hex'])
    sbe_processing.confirm_file(pack['hex'])
    sbe_processing.set_tau_state(tau)
    sbe_processing.run_process(overwrite=overwrite)
    sbe_processing.create_zip_with_psa_files()

    if config_root_directory:
        sbe_paths.set_config_root_directory(config_root_directory)
        sbe_processing.create_sensorinfo_file()
    else:
        logger.warning('No config root directory provided. Can not create sensor info file!')
