import shutil
import pathlib

from ctdpy.core import session as ctdpy_session


class NewStandardFormat:

    def __init__(self, paths_object):
        self.paths = paths_object
        self._cnv_files = []
        self._overwrite = False
        self._metadata_path = None
        self._export_directory = None

    def create_files_from_cnv(self, cnv_file_list, overwrite=False):
        self._cnv_files = cnv_file_list
        self._overwrite = bool(overwrite)

        self._create_metadata_file()
        self._create_standard_format_files()
        self._copy_standard_format_files_to_local()

    def _create_metadata_file(self):
        session = ctdpy_session.Session(filepaths=self._cnv_files,
                                        reader='smhi')
        datasets = session.read()
        dataset = datasets[0]
        session.update_metadata(datasets=dataset,
                                metadata={},
                                overwrite=self._overwrite)
        metadata_path = session.save_data(dataset,
                                          writer='metadata_template',
                                          return_data_path=True)
        self._metadata_path = pathlib.Path(metadata_path)

    def _create_standard_format_files(self):
        all_file_paths = self._cnv_files + [self._metadata_path]
        all_file_paths = [str(path) for path in all_file_paths]
        session = ctdpy_session.Session(filepaths=all_file_paths,
                                        reader='smhi')
        datasets = session.read()
        directory = session.save_data(datasets,
                                      writer='ctd_standard_template',
                                      return_data_path=True,
                                      # save_path=save_directory,
                                      )
        self._export_directory = pathlib.Path(directory)

    def _copy_standard_format_files_to_local(self):
        nsf_files = {}
        for path in self._export_directory.iterdir():
            if path.name.startswith('ctd_profile'):
                nsf_files[path.stem] = path

        target_dir = self.paths.get_local_directory('nsf', create=True)
        for cnv_file in self._cnv_files:
            split_stem = cnv_file.stem.split('_')
            date = split_stem[2]
            ship = split_stem[4]
            serno = split_stem[-1]
            nsf_file_stem = f'ctd_profile_{date}_{ship}_{serno}'
            source_path = nsf_files.get(nsf_file_stem)
            if not source_path:
                continue
            target_path = pathlib.Path(target_dir, f'{cnv_file.stem}.txt')
            shutil.copy2(source_path, target_path)


if __name__ == '__main__':
    pass
