import pathlib

from ctd_processing.ctd_files.seabird.file_pattern_nodc import NODCSBECTDFiles
from ctd_processing.ctd_files.seabird.file_pattern_old_processing_script import OldSBECTDFiles


def get_ctd_files_object(file_path):
    files_object = [
                    NODCSBECTDFiles(),
                    OldSBECTDFiles()
                    ]
    for obj in files_object:
        if obj.is_valid(file_path):
            obj.set_file_path(file_path)
            return obj


def get_matching_files_in_directory(directory):
    directory = pathlib.Path(directory)
    matching_files = {}
    for path in directory.iterdir():
        if path.stem in matching_files:
            continue
        obj = get_ctd_files_object(path)
        if not obj:
            continue
        matching_files[obj.file_path.name] = obj
    return matching_files


if __name__ == '__main__':
    f1 = r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210413_1113_77SE_00_0278.cnv'
    i1 = get_ctd_files_object(f1)

    f2 = r'C:\mw\temp_ctd_svea_aug\ctd\raw/SBE09_1387_20210814_0559_77_10_0526.hex'
    i2 = get_ctd_files_object(f2)
