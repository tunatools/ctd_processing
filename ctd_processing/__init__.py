import logging
import pathlib

import file_explorer

from ctd_processing import delivery_note
from ctd_processing import file_handler
from ctd_processing import metadata
from ctd_processing import sensor_info
from ctd_processing import standard_format
from ctd_processing.processing.sbe_processing import SBEPostProcessing
from ctd_processing.processing.sbe_processing import SBEProcessing
from ctd_processing.processing.sbe_processing import SBEProcessingHandler
from ctd_processing.processing.sbe_processing_paths import SBEProcessingPaths

logger = logging.getLogger(__name__)


def _get_metadata_from_sharkweb_btl_row_data(path, **kwargs):
    meta = {}
    metacolumns = metadata.get_metadata_columns()
    mapping = {'SLABO_PHYSCHEM': 'SLABO'}
    with open(path, encoding=kwargs.get('encoding', 'cp1252')) as fid:
        header = None
        for line in fid:
            strip_line = line.strip()
            if not strip_line:
                continue
            split_line = strip_line.split(kwargs.get('sep', '\t'))
            if not header:
                header = split_line
                continue
            d = dict(zip(header, split_line))
            key = (d['MYEAR'], d['SHIPC'], d['VISITID'].zfill(4))
            if meta.get(key):
                continue
            meta[key] = {mapping.get(key, key): value for key, value in d.items() if mapping.get(key, key) in metacolumns}
    return meta


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
    cont = SBEProcessingHandler(target_root_directory=target_root_directory, overwrite=overwrite)
    cont.set_config_root_directory(config_root_directory)
    cont.select_and_confirm_file(path)
    cont.load_psa_config_list(psa_paths)
    cont.set_options(tau=tau, platform=platform, surfacesoak=surfacesoak)
    cont.process_file()
    return cont.pack


def reprocess_sbe_file(path,
                       target_root_directory=None,
                       config_root_directory=None,
                       surfacesoak='normal',
                       tau=False,
                       overwrite=False,
                       psa_paths=None):
    """
    Reprocess seabird file using psa files stored together with raw files.
    Option to override psa files in psa_paths
    """
    path = pathlib.Path(path)
    cont = SBEProcessingHandler(target_root_directory=target_root_directory, overwrite=overwrite)
    cont.set_config_root_directory(config_root_directory)
    cont.set_options(tau=tau, surfacesoak=surfacesoak)
    cont.select_and_confirm_file(path)
    cont.load_psa_config_zip()
    cont.load_psa_config_list(psa_paths)
    cont.process_file()


def create_standard_format_for_packages(packs,
                                        target_root_directory=None,
                                        config_root_directory=None,
                                        overwrite=False,
                                        sharkweb_btl_row_file=None,
                                        **kwargs):
    """
    Use to create standard format. Creates sensorinfo file.
    """
    sharkweb_meta = {}
    if sharkweb_btl_row_file:
        sharkweb_meta = _get_metadata_from_sharkweb_btl_row_data(sharkweb_btl_row_file)

    if isinstance(packs, file_explorer.Package):
        packs = [packs]

    new_packs = []
    for pack in packs:
        meta = kwargs
        if sharkweb_meta:
            key = (pack('year'), pack('ship'), pack('serno'))
            webmeta = sharkweb_meta.get(key, {})
            if not webmeta:
                logger.info(f'No metadata in sharkweb_btl_file {sharkweb_btl_row_file} for path {pack.key}')
            else:
                meta.update(webmeta)
        post = SBEPostProcessing(pack, target_root_directory=target_root_directory, overwrite=overwrite, **meta)
        post.set_config_root_directory(config_root_directory)
        post.create_all_files()
        new_packs.append(post.pack)
    return new_packs


def create_dv_delivery(directory, output_dir):
    packs = file_explorer.get_packages_in_directory(directory, as_list=True)
    postp = SBEPostProcessing(packs, overwrite=True, output_dir=output_dir)
    postp.create_sensorinfo_summary_file()
    postp.create_metadata_file()






