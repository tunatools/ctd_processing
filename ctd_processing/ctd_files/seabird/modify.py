import pathlib

from ctd_processing import cnv

from ctd_processing.ctd_files.seabird.sbe_parent_class import SBECTDFiles


class ModifyCTDfiles(SBECTDFiles):

    def _modify_and_save_cnv_file(self, save_directory=None, overwrite=False):
        cnv_column_info_directory = pathlib.Path(pathlib.Path(__file__).parent, 'cnv_column_info')
        cnv_obj = cnv.CNVfile(ctd_files=self, cnv_column_info_directory=cnv_column_info_directory)
        cnv_obj.modify()
        file_path = pathlib.Path(save_directory, f'{self.stem}.cnv')
        cnv_obj.save_file(file_path=file_path, overwrite=overwrite)
        self._add_local_cnv_file_path(file_path)