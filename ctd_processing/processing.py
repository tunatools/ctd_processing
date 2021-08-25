import codecs
import logging
import logging.config
import os
import shutil
import subprocess
import threading
import psutil
from pathlib import Path
import datetime

# from ctd_processing import cnv
# from ctd_processing import cnv_column_info
# from ctd_processing import exceptions
# from ctd_processing import seabird
from ctd_processing import psa
from ctd_processing import ctd_files

try:
    from ctd_processing.stationnames_in_plot import insert_station_name
except:
    from stationnames_in_plot import insert_station_name


class CtdProcessing:
    """
    Config file paths are hard coded based on the root catalogue. Consider putting this info in config file (yaml, json)
    """

    def __init__(self,
                 config_root_path=None,
                 edit=False):
        self._platform = None

        self._overwrite = False
        self._edit = edit

        self._config_root_path = Path(config_root_path)
        self._local_directory = None
        self._server_directory = None

        if not self._config_root_path.exists():
            raise NotADirectoryError(self._config_root_path)

        self._ctd_files = None

    def overwrite(self, ok):
        if not self._edit:
            self._overwrite = False
        self._overwrite = bool(ok)

    @property
    def platform(self):
        return self._platform

    @platform.setter
    def platform(self, name):
        # Setting the platform. This is used for prioritising setup files in a specific folder in ctd_config\SBE\processing_psa
        if not name:
            return
        if name.lower() not in self._paths.platforms:
            raise Exception(f'Invalid platform name: {name}')
        self._platform = name
        self._paths.platform = name

    @property
    def year(self):
        if not self._ctd_files:
            return None
        return self._ctd_files.year

    def set_local_directory(self, path):
        self._local_directory = Path(path)
        self._working_directory = Path(self._local_directory, 'temp')

        self._paths = Paths(config_root_path=self._config_root_path,
                            working_directory=self._working_directory)

    def _create_temp_directory(self):
        if not self._working_directory.exists():
            os.makedirs(self._working_directory)

    def set_server_directory(self, path):
        self._server_directory = Path(path)

    def get_platfrom_options(self):
        return self._paths.platforms

    def get_surfacesoak_options(self):
        options = {}
        for path in self._paths.loopedit_paths:
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
                
    def set_surfacesoak(self, name):
        """ Sets surfacesoak in setup file. Name must match keys in coming from self.get_surfacesoak_options """
        name = name.lower()
        options = self.get_surfacesoak_options()
        for key, path in options.items():
            if name in key.lower():
                self._paths.set_loopedit(options[key])
                return (key, path)
        else:
            raise Exception('Invalid surfacesoak option')

    def _get_derive_psa_obj(self):
        # file_paths = self.get_file_paths()
        return psa.DerivePSAfile(self._paths('psa_derive'))

    def set_tau_state(self, state):
        self._get_derive_psa_obj().set_tau_correction(bool(bool))

    def select_uneditable_file(self, file_path):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        self._ctd_files = ctd_files.get_ctd_files_object(path, edit=False)

    def select_file(self, file_path):
        """ Kontrollen för att skriva över bör göras mot raw-mappen istället för mot tempmappen. """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        # Copying files and load instrument files object
        self._create_temp_directory()
        new_path = self._copy_all_files_with_same_file_stem(path, self._working_directory)
        self._ctd_files = ctd_files.get_ctd_files_object(new_path, edit=self._edit)
        self._ctd_files.rename_files(self._overwrite)
        self._paths.set_new_file_base(self._ctd_files.file_base)
        self._paths.set_config_suffix(self._ctd_files.config_file_suffix)
        self._setup_file = SetupFile(file_paths=self._paths, instrument_files=self._ctd_files)
        self._batch_file = BatchFile(file_paths=self._paths)

    def _copy_all_files_with_same_file_stem(self, file_path, target_directory):
        if not self._edit:
            raise Exception(f'Not set to edit mode!')
        stem = file_path.stem
        return_path = None
        for path in file_path.parent.iterdir():
            if path.stem == stem:
                return_path = self._copy_file(path, target_directory)
        return return_path

    def _copy_file(self, source_file_path, target_directory):
        if not self._edit:
            raise Exception(f'Not set to edit mode!')
        target_file_path = Path(target_directory, source_file_path.name)
        if target_file_path.exists() and not self._overwrite:
            raise FileExistsError(target_file_path)
        shutil.copy2(source_file_path, target_file_path)
        return target_file_path

    def get_file_names_in_server_directory(self, subfolder=None):
        if not self._server_directory:
            raise NotADirectoryError('No server directory set')
        directory = self.get_server_directory(subfolder=subfolder)
        return [path.name for path in directory.iterdir()]

    def get_local_directory(self, subfolder=None, create=False):
        return self._get_directory(self._local_directory, subfolder=subfolder, create=create)

    def get_server_directory(self, subfolder=None, create=False):
        if not self._server_directory:
            return None
        return self._get_directory(self._server_directory, subfolder=subfolder, create=create)

    def _get_directory(self, path, subfolder=None, create=False):
        if path.name != 'data':
            path = Path(path, 'data')
        if not subfolder:
            return path
        if not self.year:
            raise Exception('Could not find valid year to create local data directory!')
        path = Path(path, str(self.year))
        if subfolder == 'cnv':
            path = Path(path, 'cnv')
        elif subfolder == 'raw':
            path = Path(path, 'raw')
        elif subfolder == 'nsf':
            path = Path(path, 'nsf')
        elif subfolder:
            raise Exception(f'Invalid file subfolder: {subfolder}')
        if not path.exists() and create:
            os.makedirs(path)
        return path

    def run_process(self):
        if not self._edit:
            raise Exception(f'Not set to edit mode!')
        self._setup_file.create_file()
        self._batch_file.create_file()
        self._batch_file.run_file()
        self._ctd_files.add_processed_file_paths()
        self._ctd_files.modify_and_save_cnv_file(save_directory=self.get_local_directory('cnv', create=True), overwrite=self._overwrite)


class BatchFile:
    def __init__(self, file_paths=None):
        """
        :param file_paths: Paths
        """
        self._paths = file_paths
        self._batch_file_path = self._paths('file_batch')
        self._setup_file_path = self._paths('file_setup')
        self._working_dir = self._paths('dir_working')

    def create_file(self):
        with open(self._batch_file_path, 'w') as fid:
            fid.write(f'sbebatch.exe {self._setup_file_path} {self._working_dir}')

    def run_file(self):
        if not self._batch_file_path.exists():
            raise FileNotFoundError(f'Batch file not found: {self._batch_file_path}')
        subprocess.run(str(self._batch_file_path))
        # run_program('Seasave.exe', str(self._batch_file_path))


class SetupFile:
    def __init__(self, file_paths=None, instrument_files=None):
        """
        :param file_paths: Paths
        :param instrument_files: instrumant_files.InstrumentFiles
        """
        self._paths = file_paths
        self._ctd_files = instrument_files

    def _get_lines(self):

        lines = {}

        lines['datcnv'] = f'datcnv /p{self._paths("psa_datcnv")} /i{self._paths("hex")} /c{self._paths("config")} /o%1'
        lines['filter'] = f'filter /p{self._paths("psa_filter")} /i{self._paths("cnv")} /o%1 '
        lines['alignctd'] = f'alignctd /p{self._paths("psa_alignctd")} /i{self._paths("cnv")} /c{self._paths("config")} /o%1'

        lines['celltm'] = f'celltm /p{self._paths("psa_celltm")} /i{self._paths("cnv")} /c{self._paths("config")} /o%1'

        lines['loopedit'] = f'loopedit /p{self._paths("psa_loopedit")} /i{self._paths("cnv")} /c{self._paths("config")} /o%1'

        lines['derive'] = f'derive /p{self._paths("psa_derive")} /i{self._paths("cnv")} /c{self._paths("config")} /o%1'
        lines['binavg'] = f'binavg /p{self._paths("psa_binavg")} /i{self._paths("cnv")} /c{self._paths("config")} /o%1'

        lines['bottlesum'] = self._get_bottle_sum_line()

        lines['split'] = f'split /p{self._paths("psa_split")} /i{self._paths("cnv")} /o%1'

        lines['plot1'] = f'seaplot /p{self._paths("psa_1-seaplot")} /i{self._paths("cnv_down")} /a_{self._ctd_files.station} /o{self._paths("dir_working")} /f{self._ctd_files.proper_stem}'
        lines['plot2'] = f'seaplot /p{self._paths("psa_2-seaplot")} /i{self._paths("cnv_down")} /a_TS_diff_{self._ctd_files.station} /o{self._paths("dir_working")} /f{self._ctd_files.proper_stem}'
        lines['plot3'] = f'seaplot /p{self._paths("psa_3-seaplot")} /i{self._paths("cnv_down")} /a_oxygen_diff_{self._ctd_files.station} /o{self._paths("dir_working")} /f{self._ctd_files.proper_stem}'
        lines['plot4'] = f'seaplot /p{self._paths("psa_4-seaplot")} /i{self._paths("cnv_down")} /a_fluor_turb_par_{self._ctd_files.station} /o{self._paths("dir_working")} /f{self._ctd_files.proper_stem}'

        return list(lines.values())

    def _get_bottle_sum_line(self):
        bottlesum = ''
        if self._ctd_files.number_of_bottles and self._paths("ros"):
            bottlesum = f'bottlesum /p{self._paths("psa_bottlesum")} /i{self._paths("ros")} /c{self._paths("config")} /o%1 '
        else:
            # 'No bottles fired, will not create .btl or .ros file'
            pass
        return bottlesum
    
    def create_file(self):
        self._add_station_name_to_plots()
        self._write_lines()

    def _write_lines(self):
        file_path = self._paths('file_setup')
        all_lines = self._get_lines()
        with codecs.open(file_path, "w", encoding='cp1252') as fid:
            fid.write('\n'.join(all_lines))

    def _add_station_name_to_plots(self):
        for p in range(1, 5):
            obj = psa.PlotPSAfile(self._paths(f"psa_{p}-seaplot"))
            obj.title = self._ctd_files.station
            obj.save()


class Paths:
    """
    Class holds paths used in the SetupFile class. Paths are based on structure of the ctd_config repo.
    For the moment the paths are hardcoded according. Consider putting this information in a config file.

    """

    def __init__(self, config_root_path=None, working_directory=None):
        """ Config root path is the root path och ctd_config repo """
        self._paths = {}
        self._config_root_path = Path(config_root_path)
        self._working_directory = Path(working_directory)
        self._paths['dir_config'] = self._config_root_path
        self._paths['dir_working'] = self._working_directory
        self._paths['file_setup'] = Path(self._working_directory, 'ctdmodule.txt')
        self._paths['file_batch'] = Path(self._working_directory, 'SBE_batch.bat')

        self._platform = None
        self._new_file_base = None
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

        self._init()

    def __call__(self, key, *args, **kwargs):
        path = self._paths.get(key)
        if not path:
            raise FileNotFoundError(f'No file found matching key: {key}')
        return path

    def __str__(self):
        return_list = []
        for name in sorted(self._paths):
            return_list.append(f'{name.ljust(15)}: {self._paths[name]}')
        return '\n'.join(return_list)

    def __repr__(self):
        return self.__str__()

    def _init(self):
        self._save_platform_paths()
        self._build_psa_file_paths()
        self._build_loopedit_file_paths()

    def _save_platform_paths(self):
        self._platform_paths = {}
        for path in Path(self._config_root_path, 'SBE', 'processing_psa').iterdir():
            self._platform_paths[path.name.lower()] = path

    @property
    def loopedit_paths(self):
        return self._loopedit_paths

    @property
    def platforms(self):
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
        self._build_psa_file_paths()
        self._build_loopedit_file_paths()

    def set_new_file_base(self, new_file_base):
        self._new_file_base = new_file_base
        self._set_file_names_with_new_base()

    def _set_file_names_with_new_base(self):
        """
        Raw file can be a file with any raw file extension.
        :param raw_file_name: str
        :return:
        """
        self._build_raw_file_paths_with_new_file_base()
        self._build_cnv_file_paths_with_new_file_base()

    def _build_raw_file_paths_with_new_file_base(self):
        """ Builds the raw file paths from working directory and raw file stem """
        self._paths['config'] = Path(f'{self._new_file_base}.XMLCON')  # Handle CON-files
        self._paths['hex'] = Path(f'{self._new_file_base}.hex')
        self._paths['ros'] = Path(f'{self._new_file_base}.ros')

        for name in ['config', 'hex']:
            if not self._paths[name].exists():
                raise FileNotFoundError(self._paths[name])

    def _build_cnv_file_paths_with_new_file_base(self):
        """ Builds the cnv file paths from working directory and raw file stem """
        self._paths['cnv'] = Path(f'{self._new_file_base}.cnv')
        self._paths['cnv_down'] = Path(f'{self._new_file_base.parent}', f'd{self._new_file_base.name}.cnv')
        self._paths['cnv_up'] = Path(f'{self._new_file_base.parent}', f'u{self._new_file_base.name}.cnv')

    def _build_psa_file_paths(self):
        """
        Builds file paths for the psa files.
        If platform is present then these files ar prioritized.
        Always checking directory ctd_config/SBE/processing_psa/Common
        """
        all_paths = self._get_all_pas_paths()
        for name in self._psa_names:
            for path in all_paths:
                if name in path.name.lower():
                    self._paths[f'psa_{name}'] = path
                    break
            else:
                raise Exception(f'Could not find psa file associated with: {name}')

    def _build_loopedit_file_paths(self):
        self._loopedit_paths = []
        for path in self._get_all_pas_paths():
            name = path.name.lower()
            if 'loopedit' in name and name not in self._loopedit_paths:
                self._loopedit_paths.append(path)

    def _get_all_pas_paths(self):
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
        self._paths['config'] = Path(f'{self._new_file_base}{suffix}')


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
    p = CtdProcessing(config_root_path=r'C:\mw\git\ctd_config', edit=True
                      # local_directory=r'C:\mw\temp_ctd_pre_system_data_root\data',
                      )
    p.overwrite(True)
    p.set_local_directory(r'C:\mw\temp_ctd_pre_system_data_root\data')
    #
    # p.set_surfacesoak('deep')
    #
    p.select_file(r'C:\mw\temp_ctd_pre_system_data_root\source/SBE09_1387_20210413_1113_77_10_0278.bl')
    # p.select_file(r'C:\mw\temp_ctd_pre_system_data_root\source/SBE09_1387_20210413_1422_77SE_01_0279.bl')

    p.run_process()

    # from ctd_processing import psa
    #
    # plot = psa.PlotPSAfile(r'C:\mw\git\ctd_config\SBE\processing_psa\Common/SeaPlot_T_S_difference.psa')
