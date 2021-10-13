from ctd_processing import utils
from ctd_processing import xmlcon

from .cnv_file import CNVfile


def get_parameter_channels_and_names_from_cnv(path):
    info = {}
    with open(path) as fid:
        for line in fid:
            if not line.startswith('# name'):
                continue
            name, par = line.split('=', 1)
            par = par.strip()
            channel = int(name.strip().split()[-1])
            info[channel] = par
    return info


def get_sensor_id_and_paramater_mapping_from_cnv(path):
    xml_info = xmlcon.CNVfileXML(path).get_sensor_info()
    name_info = get_parameter_channels_and_names_from_cnv(path)
    mapping = {}
    for info in xml_info:
        mapping[info['serial_number']] = name_info.get(info['channel'], '')
    return mapping


def get_header_form_information(path):
    info = {}
    with open(path) as fid:
        for line in fid:
            if not line.startswith('**'):
                continue
            split_line = [part.strip() for part in line.strip('*').split(':', 1)]
            if len(split_line) != 2:
                continue
            info[split_line[0]] = split_line[1]
            # Special treatment for metadata
            if 'metadata' in split_line[0].lower():
                metadata = utils.metadata_string_to_dict(split_line[1])
                for key, value in metadata.items():
                    info[key] = value
    return info