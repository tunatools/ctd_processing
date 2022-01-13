import shutil
import pathlib
import datetime
import os

from ctdpy.core import session as ctdpy_session

from ctd_processing.sensor_info import create_sensor_info_files_from_cnv_files
from ctd_processing.sensor_info.sensor_info_file import SensorInfoFiles
from ctd_processing.metadata import MetadataFile
from ctd_processing.delivery_note import DeliveryNote
from ctd_processing.data_delivery import DeliveryMetadataFile
from ctd_processing import exceptions


class CreateStandardFormat:

    def __init__(self, paths_object):
        self.paths = paths_object
        self._cnv_files = []
        self._overwrite = False
        self._metadata_path = None
        self._export_directory = None
        self._output_dir = None

        self._sensorinfo_file_path = None
        self._metadata_file_path = None

        self.delivery_metadata_file_path = None

    def create_files_from_cnv(self, cnv_file_list, overwrite=False):
        if not cnv_file_list:
            return

        self._output_dir = pathlib.Path(self.paths.get_local_directory('temp'), 'delivery_files', datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        if not self._output_dir.exists():
            os.makedirs(self._output_dir)

        self.delivery_metadata_file_path = pathlib.Path(self._output_dir, 'ctd_metadata.xlsx')

        self._cnv_files = cnv_file_list
        self._overwrite = bool(overwrite)

        self._create_sensorinfo_file()
        self._create_metadata_file()
        self._create_deliverynote_file()
        # self._create_delivery_metadata_file()
        #
        self._create_standard_format_files()
        self._copy_standard_format_files_to_local()

    def _create_sensorinfo_file(self):
        create_sensor_info_files_from_cnv_files(self._cnv_files,
                                                self.paths.get_path('instrumentinfo_file'),
                                                output_dir=self._output_dir)
        sensorinfo = SensorInfoFiles(self._output_dir)
        self._sensorinfo_file_path = sensorinfo.write_summary_to_file()

    def _create_metadata_file(self):
        metadata = MetadataFile(file_list=self._cnv_files)
        self._metadata_file_path = metadata.write_to_file(self._output_dir)

    def _create_deliverynote_file(self):
        delivery = DeliveryNote(file_list=self._cnv_files,
                                contact='Magnus',
                                comment='Detta är ett test',
                                description='Testdataset')
        self._deliverynote_file_path = delivery.write_to_file(self._output_dir)

    def old_create_delivery_metadata_file(self):
        dmeta = DeliveryMetadataFile()
        dmeta.add_sensorinfo_from_file(self._sensorinfo_file_path)
        dmeta.add_metadata_from_file(self._metadata_file_path)
        dmeta.save_file(pathlib.Path(self.delivery_metadata_file_path))

    # def _old_create_metadata_file(self):
    #     session = ctdpy_session.Session(filepaths=self._cnv_files,
    #                                     reader='smhi')
    #     datasets = session.read()
    #     dataset = datasets[0]
    #     session.update_metadata(datasets=dataset,
    #                             metadata={},
    #                             overwrite=self._overwrite)
    #     metadata_path = session.save_data(dataset,
    #                                       writer='metadata_template',
    #                                       return_data_path=True)
    #     self._metadata_path = pathlib.Path(metadata_path)

    def _create_standard_format_files(self):
        all_file_paths = self._cnv_files + [self._sensorinfo_file_path, self._metadata_file_path, self._deliverynote_file_path]
        s = ctdpy_session.Session(filepaths=all_file_paths,
                                  reader='smhi')
        datasets = s.read()
        print('#'*50)
        for f in sorted(all_file_paths):
            print(f)

        data_path = s.save_data(datasets,
                                writer='ctd_standard_template',
                                keep_original_file_names=True,
                                return_data_path=True)
        
        self._export_directory = pathlib.Path(data_path)

    def _copy_standard_format_files_to_local(self):
        target_dir = self.paths.get_local_directory('nsf', create=True)
        cnv_file_stems = [path.stem for path in self._cnv_files]



        for source_path in self._export_directory.iterdir():
            if source_path.stem not in cnv_file_stems:
                continue
            target_path = pathlib.Path(target_dir, source_path.name)
            if target_path.exists() and not self._overwrite:
                raise exceptions.FileExists(target_path)
            shutil.copy2(source_path, target_path)


def has_automatic_qc_today(file_path):
    with open(file_path) as fid:
        for line in fid:
            if line.startswith('//COMNT_QC; AUTOMATIC QC'):
                split_line = line.split(';')
                time_str = split_line[2].split()[-1]
                date = datetime.datetime.strptime(time_str, '%Y%m%d%H%M').date()
                today = datetime.datetime.today().date()
                return date == today


if __name__ == '__main__':
    print(has_automatic_qc_today(r'C:\mw\temp_ctd_pre_system_data_root\data/SBE09_1387_20210415_1647_77SE_00_0293.txt'))
