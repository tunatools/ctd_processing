import codecs
import os
import shutil
import subprocess
import threading
import psutil
from pathlib import Path
import datetime
import filecmp

from abc import ABC, abstractmethod


# from ctd_processing import cnv
# from ctd_processing import cnv_column_info
# from ctd_processing import exceptions
# from ctd_processing import seabird
from ctd_processing import psa
from ctd_processing import ctd_files

from ctdpy.core import session as ctdpy_session

try:
    from ctd_processing.stationnames_in_plot import insert_station_name
except:
    from stationnames_in_plot import insert_station_name


class SBEProcessing:
    """
    Config file paths are hard coded based on the root catalogue. Consider putting this info in config file (yaml, json)
    """

    def __init__(self, sbe_paths=None, sbe_processing_paths=None):
        self._paths = sbe_paths
        self._processing_paths = sbe_processing_paths

        self._platform = None
        self._file_path = None
        self._confirmed = False
        self._overwrite = False
        self._ctd_files = None

    @property
    def platform(self):
        return self._platform

    @platform.setter
    def platform(self, name):
        # Setting the platform. This is used for prioritising setup files in a specific folder in ctd_config\SBE\processing_psa
        if not name:
            return
        if name.lower() not in self._processing_paths.platforms:
            raise Exception(f'Invalid platform name: {name}')
        self._platform = name
        self._paths.platform = name

    @property
    def year(self):
        if not self._ctd_files:
            return None
        return self._ctd_files.year

    def get_platform_options(self):
        return self._processing_paths.platforms

    def get_surfacesoak_options(self):
        options = {}
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
        self._platform = platform

    def set_surfacesoak(self, name):
        """ Sets surfacesoak in setup file. Name must match keys in coming from self.get_surfacesoak_options """
        name = name.lower()
        options = self.get_surfacesoak_options()
        for key, path in options.items():
            if name in key.lower():
                self._processing_paths.set_loopedit(options[key])
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
        path = Path(file_path)
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
        path = Path(file_path)
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
                      key in self._ctd_files.raw_files_extensions]
        for file_path in file_paths:
            self._copy_file(file_path, target_directory, overwrite=self._overwrite)

    def _copy_cnv_files_to_local(self):
        """ Copies cnv-up file to local directory """
        target_directory = self._paths.get_local_directory('cnv_up', create=True)
        self._copy_file(self._ctd_files('cnv_up'), target_directory, overwrite=self._overwrite)

    def _copy_plot_files_to_local(self):
        target_directory = self._paths.get_local_directory('plot', create=True)
        for file_path in self._ctd_files.plot_files:
            self._copy_file(file_path, target_directory, overwrite=self._overwrite)

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

    def _copy_file(self, source_file_path, target_directory, overwrite=False):
        target_file_path = Path(target_directory, source_file_path.name)
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
        self._ctd_files.add_processed_file_paths()
        self._ctd_files.modify_and_save_cnv_file(save_directory=self._paths.get_local_directory('cnv', create=True),
                                                 overwrite=self._overwrite)
        self._copy_processed_files_to_local()


class SBEBatchFile:
    def __init__(self, paths=None, processing_paths=None):
        """
        :param file_paths: SBEProsessingPaths
        """
        self._paths = paths
        self._processing_paths = processing_paths

    def create_file(self):
        with open(self._processing_paths('file_batch'), 'w') as fid:
            fid.write(f"sbebatch.exe {self._processing_paths('file_setup')} {self._paths('working_dir')}")

    def run_file(self):
        if not self._processing_paths('file_batch').exists():
            raise FileNotFoundError(f"Batch file not found: {self._processing_paths('file_batch')}")
        subprocess.run(str(self._processing_paths('file_batch')))


class SBESetupFile:
    def __init__(self, paths=None, processing_paths=None, instrument_files=None):
        """
        :param file_paths: SBEProsessingPaths
        :param instrument_files: instrumant_files.InstrumentFiles
        """
        self._proc_paths = processing_paths
        self._paths = paths
        self._ctd_files = instrument_files

    def _get_lines(self):

        lines = {}

        lines['datcnv'] = f'datcnv /p{self._proc_paths("psa_datcnv")} /i{self._proc_paths("hex")} /c{self._proc_paths("config")} /o%1'
        lines['filter'] = f'filter /p{self._proc_paths("psa_filter")} /i{self._proc_paths("cnv")} /o%1 '
        lines['alignctd'] = f'alignctd /p{self._proc_paths("psa_alignctd")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'

        lines['celltm'] = f'celltm /p{self._proc_paths("psa_celltm")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'

        lines['loopedit'] = f'loopedit /p{self._proc_paths("psa_loopedit")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'

        lines['derive'] = f'derive /p{self._proc_paths("psa_derive")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'
        lines['binavg'] = f'binavg /p{self._proc_paths("psa_binavg")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'

        lines['bottlesum'] = self._get_bottle_sum_line()

        lines['split'] = f'split /p{self._proc_paths("psa_split")} /i{self._proc_paths("cnv")} /o%1'

        lines['plot1'] = f'seaplot /p{self._proc_paths("psa_1-seaplot")} /i{self._proc_paths("cnv_down")} /a_{self._ctd_files.station} /o{self._paths("working_dir")} /f{self._ctd_files.proper_stem}'
        lines['plot2'] = f'seaplot /p{self._proc_paths("psa_2-seaplot")} /i{self._proc_paths("cnv_down")} /a_TS_diff_{self._ctd_files.station} /o{self._paths("working_dir")} /f{self._ctd_files.proper_stem}'
        lines['plot3'] = f'seaplot /p{self._proc_paths("psa_3-seaplot")} /i{self._proc_paths("cnv_down")} /a_oxygen_diff_{self._ctd_files.station} /o{self._paths("working_dir")} /f{self._ctd_files.proper_stem}'
        lines['plot4'] = f'seaplot /p{self._proc_paths("psa_4-seaplot")} /i{self._proc_paths("cnv_down")} /a_fluor_turb_par_{self._ctd_files.station} /o{self._paths("working_dir")} /f{self._ctd_files.proper_stem}'

        return list(lines.values())

    def _get_bottle_sum_line(self):
        bottlesum = ''
        if self._ctd_files.number_of_bottles and self._proc_paths("ros"):
            bottlesum = f'bottlesum /p{self._proc_paths("psa_bottlesum")} /i{self._proc_paths("ros")} /c{self._proc_paths("config")} /o%1 '
        else:
            # 'No bottles fired, will not create .btl or .ros file'
            pass
        return bottlesum
    
    def create_file(self):
        self._add_station_name_to_plots()
        self._write_lines()

    def _write_lines(self):
        file_path = self._proc_paths('file_setup')
        all_lines = self._get_lines()
        with codecs.open(file_path, "w", encoding='cp1252') as fid:
            fid.write('\n'.join(all_lines))

    def _add_station_name_to_plots(self):
        #for key in sorted(self._proc_paths._paths):
        #    print(key)
        for p in range(1, 5):
            obj = psa.PlotPSAfile(self._proc_paths(f"psa_{p}-seaplot"))
            obj.title = self._ctd_files.station
            obj.save()


class SBEProcessingPaths:
    """
    Class holds paths used in the SBESetupFile class. SBEProsessingPaths are based on structure of the ctd_config repo.
    For the moment the paths are hardcoded according. Consider putting this information in a config file.

    """

    def __init__(self, sbe_paths=None):
        """ Config root path is the root path och ctd_config repo """
        self._paths = {}

        self.sbe_paths = sbe_paths

        self._platform = None
        self._new_file_stem = None
        self._loopedit_paths = []
        self._psa_names = ['datcnv',
                           'filter',
                           'alignctd',
                           'bottlesum',
                           'celltm',
                           'derive',
                           'binavg',
                           'loopedit',
                           'split',
                           '1-seaplot',
                           '2-seaplot',
                           '3-seaplot',
                           '4-seaplot']
        self.update_paths()

    def __call__(self, key, create=False, **kwargs):
        path = self._paths.get(key)
        if not path:
            raise FileNotFoundError(f'No file found matching key: {key}')
        if create and not path.exists():
            os.makedirs(str(path))
        return path

    def __str__(self):
        return_list = []
        for name in sorted(self._paths):
            return_list.append(f'{name.ljust(15)}: {self._paths[name]}')
        return '\n'.join(return_list)

    def __repr__(self):
        return self.__str__()

    def _save_platform_paths(self):
        """
        Platform paths are based on directories under <congif path>/SBE/proseccing_psa.
        Files in the subfolders are specific for the corresponding "platform"
        """
        self._platform_paths = {}
        for path in Path(self.sbe_paths('config_dir'), 'SBE', 'processing_psa').iterdir():
            self._platform_paths[path.name.lower()] = path

    def update_paths(self):
        self._paths['file_setup'] = Path(self.sbe_paths('working_dir'), 'ctdmodule.txt')
        self._paths['file_batch'] = Path(self.sbe_paths('working_dir'), 'SBE_batch.bat')
        self._save_platform_paths()

        if self._new_file_stem:
            self._build_raw_file_paths_with_new_file_stem()
            self._build_cnv_file_paths_with_new_file_stem()

        if self._platform:
            self._build_psa_file_paths()
            self._build_loopedit_file_paths()

    @property
    def loopedit_paths(self):
        self.update_paths()
        return self._loopedit_paths

    @property
    def platforms(self):
        self.update_paths()
        exclude = ['archive', 'common']
        return [name for name in self._platform_paths if name not in exclude]

    @property
    def platform(self):
        return self._platform

    @platform.setter
    def platform(self, platform):
        plat = platform.lower()
        if plat not in self.platforms:
            raise Exception(f'Invalid platform for SBE processing_psa: {platform}')
        self._platform = plat
        self.update_paths()

    def set_raw_file_path(self, file_path):
        """
        Sets file path for the raw files.
        """
        self._new_file_stem = file_path.stem
        self.update_paths()

    def _build_raw_file_paths_with_new_file_stem(self):
        """ Builds the raw file paths from working directory and raw file stem """
        print("self.sbe_paths('working_dir')", self.sbe_paths('working_dir'))
        self._paths['config'] = Path(self.sbe_paths('working_dir'), f'{self._new_file_stem}.XMLCON')  # Handle CON-files
        self._paths['hex'] = Path(self.sbe_paths('working_dir'), f'{self._new_file_stem}.hex')
        self._paths['ros'] = Path(self.sbe_paths('working_dir'), f'{self._new_file_stem}.ros')

        for name in ['config', 'hex']:
            if not self._paths[name].exists():
                raise FileNotFoundError(self._paths[name])

    def _build_cnv_file_paths_with_new_file_stem(self):
        """ Builds the cnv file paths from working directory and raw file stem """
        self._paths['cnv'] = Path(self.sbe_paths('working_dir'), f'{self._new_file_stem}.cnv')
        self._paths['cnv_down'] = Path(self.sbe_paths('working_dir'), f'd{self._new_file_stem}.cnv')
        self._paths['cnv_up'] = Path(self.sbe_paths('working_dir'), f'u{self._new_file_stem}.cnv')

    def _build_psa_file_paths(self):
        """
        Builds file paths for the psa files.
        If platform is present then these files ar prioritized.
        Always checking directory ctd_config/SBE/processing_psa/Common
        """
        all_paths = self._get_all_psa_paths()
        for name in self._psa_names:
            for path in all_paths:
                if name in path.name.lower():
                    self._paths[f'psa_{name}'] = path
                    break
            else:
                raise Exception(f'Could not find psa file associated with: {name}')

    def _build_loopedit_file_paths(self):
        self._loopedit_paths = []
        for path in self._get_all_psa_paths():
            name = path.name.lower()
            if 'loopedit' in name and name not in self._loopedit_paths:
                self._loopedit_paths.append(path)

    def _get_all_psa_paths(self):
        """
        Returns a list of all psa paths.
        If platform is present then these files ar prioritized.
        Always include paths in directory ctd_config/SBE/processing_psa/Common
        """
        all_paths = []
        if self._platform:
            all_paths.extend(self._get_paths_in_directory(self._platform_paths[self._platform]))
        all_paths.extend(self._get_paths_in_directory(self._platform_paths['common']))
        return all_paths

    @staticmethod
    def _get_paths_in_directory(directory):
        return [path for path in directory.iterdir()]

    def set_loopedit(self, path):
        """ Manually setting the loopedit file """
        path = Path(path)
        if 'loopedit' not in path.name.lower():
            raise Exception(f'Invalid LoopEdit file: {path}')
        elif not path.exists():
            raise FileNotFoundError(path)
        self._paths['psa_loopedit'] = path

    def set_config_suffix(self, suffix):
        self._paths['config'] = Path(self.sbe_paths('working_dir'), f'{self._new_file_stem}{suffix}')


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
        self._metadata_path = Path(metadata_path)

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
        self._export_directory = Path(directory)

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
            target_path = Path(target_dir, f'{cnv_file.stem}.nsf')
            shutil.copy2(source_path, target_path)


def _get_running_programs():
    program_list = []
    for p in psutil.process_iter():
        program_list.append(p.name())
    return program_list


def _run_subprocess(line):
    subprocess.run(line)


def run_program(program, line):
    if program in _get_running_programs():
        raise ChildProcessError(f'{program} is already running!')
    t = threading.Thread(target=_run_subprocess(line))
    t.daemon = True  # close pipe if GUI process exits
    t.start()


# def get_paths_in_directory(directory, match_string='', walk=False):
#     paths = {}
#     if walk:
#         for root, dirs, files in os.walk(directory, topdown=True):
#             for file_name in files:
#                 if match_string in file_name:
#                     paths[file_name] = Path(root, file_name)
#     else:
#         for file_name in os.listdir(directory):
#             if match_string in file_name:
#                 paths[file_name] = Path(directory, file_name)
#     return paths


if __name__ == '__main__':

    if 0:
        sbe_paths = SBEPaths()
        sbe_paths.set_config_root_directory(r'C:\mw\git\ctd_config')
        sbe_paths.set_local_root_directory(r'C:\mw\temp_ctd_pre_system_data_root')
        sbe_processing_paths = SBEProcessingPaths(sbe_paths)
        sbe_processing_paths.platform = 'svea'

        p = SBEProcessing(sbe_paths=sbe_paths,
                          sbe_processing_paths=sbe_processing_paths)
        p.overwrite(True)
        #
        # p.set_surfacesoak('deep')
        #
        p.select_file(r'C:\mw\temp_ctd_pre_system_data_root\source/SBE09_1387_20210413_1113_77_10_0278.bl')
        p.confirm_file(r'C:\mw\temp_ctd_pre_system_data_root\source/SBE09_1387_20210413_1113_77_10_0278.bl')
        # p.select_file(r'C:\mw\temp_ctd_pre_system_data_root\source/SBE09_1387_20210413_1422_77SE_01_0279.bl')

        p.run_process()

        # from ctd_processing import psa
        #
        # plot = psa.PlotPSAfile(r'C:\mw\git\ctd_config\SBE\processing_psa\Common/SeaPlot_T_S_difference.psa')
