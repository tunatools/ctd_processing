import codecs
import logging
import logging.config
import os
import shutil
import subprocess
from pathlib import Path

from ctd_processing import cnv
from ctd_processing import cnv_column_info
from ctd_processing import exceptions
from ctd_processing import seabird

try:
    from ctd_processing.stationnames_in_plot import insert_station_name
except:
    from stationnames_in_plot import insert_station_name


class CtdProcessing:
    def __init__(self, root_directory=None, **kwargs):

        self._surfacesoak = kwargs.get('surfacesoak', '')
        self.name = Path(__file__).stem
        self.overwrite = kwargs.get('overwrite', False)
        self.use_cnv_info_format = kwargs.get('use_cnv_info_format', False)

        self.logger = kwargs.get('logger')
        if not self.logger:
            self.logging_level = 'WARNING'
            self.logging_format = '%(asctime)s [%(levelname)10s]    %(pathname)s [%(lineno)d] => %(funcName)s():    %(message)s'
            self._setup_logger(**kwargs)

        # Directories
        self.paths = Paths(root_directory)
        self.cnv_column_info_directory = Path(Path(__file__).parent, 'cnv_column_info')
        self.cnv_info_files = cnv_column_info.CnvInfoFiles(self.cnv_column_info_directory)

        # Välj CTD
        self._ctd_number = None
        self.ctd_config_suffix = None

        self.seabird_files = None
        self.serial_number = None
        self.ship_short_name = None
        self.ship_id = None
        self.ctry = None
        self.ship = None
        self.new_file_stem = None
        self.station_name = None
        self.number_of_bottles = None
        self.year = None

        self.setup_file_object = SetupFile(parent=self)
        self.batch_file_object = BatchFile(parent=self)

        self.ctd_number = None
        self.cnv_info_object = None
        self.modify_cnv_file_object = None

        self.ctd_number = kwargs.get('ctd_number', None)

    @property
    def options(self):
        return {'root_directory': str,
                'surfacesoak': self.surfacesoak_options,
                'ctd_number': self.ctd_number_options,
                'use_cnv_info_format': bool,
                'overwrite': bool}

    def _setup_logger(self, **kwargs):
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.logging_level)
        file_path = kwargs.get('logging_file_path')
        if not file_path:
            directory = Path(__file__).absolute().parent
            if not directory.exists():
                os.makedirs(directory)
            file_path = Path(directory, f'{self.name}.log')
        handler = logging.FileHandler(str(file_path))
        # handler = TimedRotatingFileHandler(str(file_path), when='D', interval=1, backupCount=7)
        formatter = logging.Formatter(self.logging_format)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _load_cnv_info_object(self):
        self.cnv_info_object = self.cnv_info_files.get_info(self.ctd_number)

    @property
    def root_directory(self):
        return self.paths.root_directory
    
    @root_directory.setter
    def root_directory(self, directory):
        self.logger.debug(f'Setting root_directory to: {directory}')
        self.paths.root_directory = directory
        self._copy_setup_files()

    @property
    def ctd_number(self):
        return self._ctd_number

    @ctd_number.setter
    def ctd_number(self, number):
        if not number:
            return
        self._ctd_number = str(number)
        self.logger.debug(f'Setting ctd_number to: {self._ctd_number}')
        if self._ctd_number == '0817':
            self.ctd_config_suffix = '.CON'
        else:
            self.ctd_config_suffix = '.XMLCON'
        self._load_cnv_info_object()

    @property
    def surfacesoak_options(self):
        return self.setup_file_object.surfacesoak_options[:]

    @property
    def surfacesoak(self):
        return self._surfacesoak

    @surfacesoak.setter
    def surfacesoak(self, value):
        self._surfacesoak = value
        self.logger.debug(f'Setting surfacesoak to: {self._surfacesoak}')
        self.setup_file_object.surfacesoak = self._surfacesoak

    @property
    def ctd_number_options(self):
        return self.cnv_info_files.files

    def _save_info_from_seabird_files(self):
        self.serial_number = self.seabird_files.serial_number
        self.ship_short_name = self.seabird_files.ship_short_name
        self.ship_id = self.seabird_files.ship_id
        self.ctry = self.seabird_files.ctry
        self.ship = self.seabird_files.ship
        self.new_file_stem = self.seabird_files.new_file_stem
        self.station_name = self.seabird_files.station_name
        self.number_of_bottles = self.seabird_files.number_of_bottles
        self.year = self.seabird_files.date.year
        
    def _copy_setup_files(self):
        source_dir = Path(Path(__file__).parent, 'setup')
        target_dir = self.paths.get_directory('setup')
        for source_path in source_dir.iterdir():
            target_path = Path(target_dir, source_path.name)
            if target_path.exists():
                if not self.overwrite:
                    self.logger.debug(f'Not overwriting file: {target_path}')
                    continue
                os.remove(target_path)
            shutil.copy2(source_path, target_path)

    def _copy_seabird_files(self, file_path):
        """
        Copies seabird files if not already in temp directory.
        :param file_path: any seabird file with or without suffix.
        :return:
        """
        file_path = Path(file_path)
        if file_path.parent == self.paths.get_directory('temp'):
            return

        temp_path = self.paths.get_directory('working')
        file_stem = file_path.stem
        for f in file_path.parent.iterdir():
            if f.stem == file_stem:
                new_path = Path(temp_path, f.name)
                if new_path.exists() and not self.overwrite:
                    raise exceptions.FileExists(new_path)
                shutil.copy2(f, new_path)
        return new_path

    def run_process(self, server_path=None):
        self.logger.debug('Running')
        self.create_setup_and_batch_files()
        self.run_seabird()
        self.modify_cnv_file()
        self.save_modified_ctd_file()
        self.move_raw_files()
        self.remove_files()
        self.copy_files_to_server(server_path)

    def load_seabird_files(self, file_path):
        # File path can be any seabird raw file. Even without suffix.
        self.logger.debug(f'Loading file: {file_path}')
        if not self.ctd_number:
            raise exceptions.InvalidInstrumentSerialNumber('No CTD number set')

        new_path = self._copy_seabird_files(file_path)

        self.seabird_files = seabird.SeabirdFiles(new_path, self.ctd_number)
        self.seabird_files.rename_files(overwrite=self.overwrite)
        self._save_info_from_seabird_files()

    def create_setup_and_batch_files(self):
        """
        Create a text file that will be called by the bat-file.
        The file runs the SEB-programs
        """
        self.logger.debug('Running')
        self.setup_file_object.parent = self
        self.setup_file_object.surfacesoak = self.surfacesoak
        self.setup_file_object.create_file()
        self.batch_file_object.create_file()

    def run_seabird(self):
        self.logger.debug('Running')
        self.batch_file_object.run_file()
        cnv_down_file_path = self.setup_file_object.paths['cnv_down']
        self.modify_cnv_file_object = cnv.CNVfile(cnv_down_file_path, ctd_processing_object=self)

    def modify_cnv_file(self):
        self.logger.debug('Running')
        self.modify_cnv_file_object.modify()

    def save_modified_ctd_file(self):
        self.logger.debug('Running')
        file_name = str(self.modify_cnv_file_object.file_path.name)[1:]
        directory = self.paths.get_directory('data')
        # directory = Path(self.paths.get_directory('data'), str(self.year))
        file_path = Path(directory, file_name)
        self.modify_cnv_file_object.save_file(file_path, overwrite=self.overwrite)

    def remove_files(self):
        os.remove(self.setup_file_object.paths.get('cnv_down'))
        os.remove(self.setup_file_object.paths.get('cnv'))

    def move_raw_files(self):
        self.logger.debug('Running')
        year = str(self.year)
        # upcast_dir = Path(self.paths.get_directory('data'), year, 'up_cast')
        upcast_dir = Path(self.paths.get_directory('data'), 'up_cast')
        if not upcast_dir.exists():
            os.makedirs(upcast_dir)
        # raw_files_dir = Path(self.paths.get_directory('raw'), year)
        raw_files_dir = self.paths.get_directory('raw')
        upcast_file_path = self.setup_file_object.paths.get('cnv_up')
        new_upcast_file_path = Path(upcast_dir, upcast_file_path.name)
        if new_upcast_file_path.exists():
            if not self.overwrite:
                raise exceptions.FileExists
            else:
                os.remove(new_upcast_file_path)
        shutil.move(upcast_file_path, new_upcast_file_path)
        self.seabird_files.move_files(raw_files_dir, overwrite=self.overwrite)

    def copy_files_to_server(self, server_path=None):
        self.logger.debug(f'Copying files to server: {server_path}')
        if not server_path:
            self.logger.warning('No server path given')
            return
        year = str(self.year)
        server_path = Path(server_path)

        server_directories = {}
        for d in ['data', 'plots', 'raw']:
            path = Path(server_path, d, year)
            server_directories[d] = path
            if not path.exists():
                os.makedirs(path)

        file_id_string = str(self.modify_cnv_file_object.file_path.stem).split('_', 1)[-1]

        # Data files
        paths = get_paths_in_directory(Path(self.paths.get_directory('data'), year), match_string=file_id_string, walk=True)
        for file_name, path in paths.items():
            self.logger.debug(f'Copying file to server: {path}')
            if file_name.startswith('u'):
                target_path = Path(server_directories['data'], 'up_cast', file_name)
            else:
                target_path = Path(server_directories['data'], file_name)
            if not target_path.parent.exists():
                os.makedirs(target_path.parent)
            try:
                shutil.copy2(path, target_path)
            except:
                self.logger.warning(f'Could not copy file to server: {path} => {target_path}')

        # Raw files
        for file in self.seabird_files.files.values():
            target_path = Path(server_directories['raw'], file.file_name)
            try:
                shutil.copy2(file.file_path, target_path)
            except:
                self.logger.warning(f'Could not copy file to server: {file.file_path} => {target_path}')

        # Plots
        paths = get_paths_in_directory(Path(self.paths.get_directory('plot'), year), match_string=file_id_string)
        for path in paths.values():
            target_path = Path(server_directories['plots'], path.name)
            try:
                shutil.copy2(path, target_path)
            except:
                self.logger.warning(f'Could not copy file to server: {path} => {target_path}')


class Paths:
    def __init__(self, root_directory=None):

        self.directories = {}
        self.files = {}

        for d in ['root', 'working', 'setup', 'data', 'raw', 'plot']:
            self.directories[d] = None

        for f in ['ctdmodule', 'batch']:
            self.files[f] = None

        self.ctdmodule_file = 'ctdmodule.txt'
        self._file = 'SBE_batch.bat'

        if root_directory is not None:
            self.root_directory = root_directory
            
    def __repr__(self):
        str_list = ['Nuvarande mappar är:']
        for key, path in self.directories.items():
            str_list.append(f'    {key: <15}: {path}')
        str_list.append('Nuvarande filer är:')
        for key, path in self.files.items():
            str_list.append(f'    {key: <15}: {path}')
        return '\n'.join(str_list)

    @property
    def root_directory(self):
        return self.directories.get('root')

    @root_directory.setter
    def root_directory(self, directory):
        if directory is None:
            return
        root = Path(directory)
        self.directories['root'] = root
        self.directories['working'] = Path(root, 'temp')
        self.directories['setup'] = Path(root, 'setup')
        self.directories['data'] = Path(root, 'cnv')
        self.directories['raw'] = Path(root, 'raw_files')
        self.directories['plot'] = Path(root, 'plot')

        # Create folders if non existing 
        for key, path in self.directories.items():
            if not path.exists():
                os.makedirs(path)

        self.files['setup'] = Path(root, 'ctdmodule.txt')
        self.files['batch'] = Path(root, 'SBE_batch.bat')

    def get_file_path(self, file_id):
        return self.files.get(file_id)

    def get_directory(self, dir_id):
        return self.directories.get(dir_id, None)


class BatchFile:
    def __init__(self, parent):
        self.parent = parent

    def create_file(self):
        self.batch_file_path = self.parent.paths.get_file_path('batch')
        self.setup_file_path = self.parent.paths.get_file_path('setup')
        self.working_dir = self.parent.paths.get_directory('working')

        with open(self.batch_file_path, 'w') as fid:
            fid.write(f'sbebatch.exe {self.setup_file_path} {self.working_dir}')

    def run_file(self):
        if not self.batch_file_path.exists():
            raise exceptions.PathError(f'Batch file not found: {self.batch_file_path}')
        # os.system(self.batch_file_path)
        subprocess.run(str(self.batch_file_path))


class SetupFile:
    def __init__(self, parent):

        self._parent = None

        self.surfacesoak_options = ['', 'deep', 'manual', '0.3', '0.5']
        self._surfacesoak = None

        self.paths = {}

        try:
            self.parent = parent
        except:
            pass

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent
        self._save_variables()
        self._set_ship_id_str()
        self._set_paths()

    def create_file(self):
        self._save_variables()
        self._create_lines()
        self._write_lines()
        self._add_station_name_to_plots()

    def _save_variables(self):
        self.setup_directory = self.parent.paths.get_directory('setup')
        self.working_directory = self.parent.paths.get_directory('working')
        self.plot_directory = self.parent.paths.get_directory('plot')
        self.setup_file_path = self.parent.paths.get_file_path('setup')

        self.ship_id = self.parent.ship_id
        self.ctd_number = self.parent.ctd_number
        self.new_file_stem = self.parent.new_file_stem
        self.ctd_config_suffix = self.parent.ctd_config_suffix
        self.number_of_bottles = self.parent.number_of_bottles
        self.year = self.parent.year
        self.station_name = self.parent.station_name

    @property
    def surfacesoak(self):
        return self._surfacesoak

    @surfacesoak.setter
    def surfacesoak(self, value):
        if value not in self.surfacesoak_options:
            raise exceptions.InvalidSurfacesoak(value)
        value = str(value)
        self._surfacesoak = value

    def _set_paths(self):

        self.paths['ctd_config'] = Path(self.working_directory, self.new_file_stem + self.ctd_config_suffix)
        self.paths['hex'] = Path(self.working_directory, f'{self.new_file_stem}.hex')
        self.paths['ros'] = Path(self.working_directory, f'{self.new_file_stem}.ros')
        self.paths['cnv'] = Path(self.working_directory, f'{self.new_file_stem}.cnv')
        self.paths['cnv_down'] = Path(self.working_directory, f'd{self.new_file_stem}.cnv')
        self.paths['cnv_up'] = Path(self.working_directory, f'u{self.new_file_stem}.cnv')

        self.paths['psa_datacnv'] = Path(self.setup_directory, f'DatCnv{self.ship_id_str}.psa')
        self.paths['psa_filter'] = Path(self.setup_directory, f'Filter{self.ship_id_str}.psa')
        self.paths['psa_alignctd'] = Path(self.setup_directory, f'AlignCTD{self.ship_id_str}.psa')
        self.paths['psa_bottlesum'] = Path(self.setup_directory, f'BottleSum{self.ship_id_str}.psa')

        self.paths['psa_celltm'] = Path(self.setup_directory, 'CellTM.psa')
        self.paths['psa_derive'] = Path(self.setup_directory, 'Derive.psa')
        self.paths['psa_binavg'] = Path(self.setup_directory, 'BinAvg.psa')

        if self.ship_id == '26_01':
            self.paths['psa_loopedit'] = Path(self.setup_directory, f'LoopEdit{self.ship_id_str}.psa')
        elif self.surfacesoak == 'deep':
            self.paths['psa_loopedit'] = Path(self.setup_directory, f'LoopEdit_deep.psa')
        elif self.surfacesoak == 'manual':
            self.paths['psa_loopedit'] = Path(self.setup_directory, f'LoopEdit_shallow.psa')
            # self.paths['psa_loopedit'] = Path(self.setup_directory, f'LoopEdit_manuell_surfacesoak.psa')
        elif self.surfacesoak:
            self.paths['psa_loopedit'] = Path(self.setup_directory, f'LoopEdit{self.surfacesoak}ms.psa')
        else:
            # 'running loopedit with minimum 0.15 m/s'
            self.paths['psa_loopedit'] = Path(self.setup_directory, f'LoopEdit.psa')

        if self.ship_id_str == '_Svea':
            self.paths['psa_split'] = Path(self.setup_directory, f'Split{self.ship_id_str}.psa')
        else:
            self.paths['psa_split'] = Path(self.setup_directory, 'Split.psa')

        self.paths['psa_plot1'] = Path(self.setup_directory, 'File_1-SeaPlot.psa')
        self.paths['psa_plot2'] = Path(self.setup_directory, 'File_2-SeaPlot_T_S_difference.psa')
        self.paths['psa_plot3'] = Path(self.setup_directory, 'File_3-SeaPlot_oxygen1&2.psa')
        if self.ship_id in ['26_01', '77_10']:
            self.paths['psa_plot4'] = Path(self.setup_directory, f'File_4-SeaPlot_TURB_PAR{self.ship_id_str}.psa')
        else:
            self.paths['psa_plot4'] = Path(self.setup_directory, 'File_4-SeaPlot_TURB_PAR.psa')

    def _set_ship_id_str(self):
        self.ship_id_str = ''
        # Dana
        if self.ship_id == '26_01':
            self.ship_id_str = '_DANA'
        # FMI
        elif self.ctd_number == '0817':
            self.ship_id_str = '_FMI'
        # Svea
        elif self.ctd_number in ['1387', '1044', '0745']:
            self.ship_id_str = '_Svea'

    def _create_lines(self):

        self.lines = dict()

        self.lines['datacnv'] = f'datcnv /p{self.paths["psa_datacnv"]} /i{self.paths["hex"]} /c{self.paths["ctd_config"]} /o%1'
        self.lines['filter'] = f'filter /p{self.paths["psa_filter"]} /i{self.paths["cnv"]} /o%1 '
        self.lines['alignctd'] = f'alignctd /p{self.paths["psa_alignctd"]} /i{self.paths["cnv"]} /c{self.paths["ctd_config"]} /o%1'

        self.lines['celltm'] = f'celltm /p{self.paths["psa_celltm"]} /i{self.paths["cnv"]} /c{self.paths["ctd_config"]} /o%1'

        self.lines['loopedit'] = f'loopedit /p{self.paths["psa_loopedit"]} /i{self.paths["cnv"]} /c{self.paths["ctd_config"]} /o%1'

        self.lines['derive'] = f'derive /p{self.paths["psa_derive"]} /i{self.paths["cnv"]} /c{self.paths["ctd_config"]} /o%1'
        self.lines['binavg'] = f'binavg /p{self.paths["psa_binavg"]} /i{self.paths["cnv"]} /c{self.paths["ctd_config"]} /o%1'

        self.lines['bottlesum'] = self._get_bottle_sum_line()

        # Strip
        # Tar bort O2 raw som används för beräkning av 02
        # borttaget JK, 02 okt 2019
        # self.strip = 'strip /p{self.setup_directory}\Strip.psa /i{self.paths["cnv"]} /o%1 \n'
        # module_file.write(self.strip)

        self.lines['split'] = f'split /p{self.paths["psa_split"]} /i{self.paths["cnv"]} /o%1'

        # Use a modified cnv file path here
        cnv_file_path = Path(self.working_directory, f'd{self.new_file_stem}.cnv')
        plot_directory = Path(self.plot_directory, str(self.year))
        if not plot_directory.exists():
            os.makedirs(plot_directory)
        self.lines['plot1'] = f'seaplot /p{self.paths["psa_plot1"]} /i{cnv_file_path} /a_{self.station_name} /o{plot_directory} /f{self.new_file_stem}'
        self.lines['plot2'] = f'seaplot /p{self.paths["psa_plot2"]} /i{cnv_file_path} /a_TS_diff_{self.station_name} /o{plot_directory} /f{self.new_file_stem}'
        self.lines['plot3'] = f'seaplot /p{self.paths["psa_plot3"]} /i{cnv_file_path} /a_oxygen_diff_{self.station_name} /o{plot_directory} /f{self.new_file_stem}'
        self.lines['plot4'] = f'seaplot /p{self.paths["psa_plot4"]} /i{cnv_file_path} /a_fluor_turb_par_{self.station_name} /o{plot_directory} /f{self.new_file_stem}'

    def _get_bottle_sum_line(self):
        bottlesum = ''
        if self.number_of_bottles:
            bottlesum = f'bottlesum /p{self.paths["psa_bottlesum"]} /i{self.paths["ros"]} /c{self.paths["ctd_config"]} /o%1 '
        else:
            # 'No bottles fired, will not create .btl or .ros file'
            pass
        return bottlesum

    def get_all_lines(self):
        return [value for key, value in self.lines.items() if value]

    def _write_lines(self):
        all_lines = self.get_all_lines()
        with codecs.open(self.setup_file_path, "w", encoding='cp1252') as fid:
            fid.write('\n'.join(all_lines))

    def _add_station_name_to_plots(self):
        # Skriv in stationsnamn i varje plot
        insert_station_name(self.station_name, str(self.paths['psa_plot1']))
        insert_station_name(self.station_name, str(self.paths['psa_plot2']))
        insert_station_name(self.station_name, str(self.paths['psa_plot3']))
        insert_station_name(self.station_name, str(self.paths['psa_plot4']))


def get_paths_in_directory(directory, match_string='', walk=False):
    paths = {}
    if walk:
        for root, dirs, files in os.walk(directory, topdown=True):
            for file_name in files:
                if match_string in file_name:
                    paths[file_name] = Path(root, file_name)
    else:
        for file_name in os.listdir(directory):
            if match_string in file_name:
                paths[file_name] = Path(directory, file_name)
    return paths


if __name__ == '__main__':
    ctdp = CtdProcessing()
    ctdp.root_directory = r'C:\mw\temp_ctd_processing'
    ctdp.ctd_number = 1387
    ctdp.overwrite = True
    ctdp.use_cnv_info_format = True
    ctdp.surfacesoak = ''
    # ctdp.load_seabird_files(r'C:\mw\data\sbe_raw_files\SBE09_1387_20200816_1055_77_10_0496')
    ctdp.load_seabird_files(r'C:\mw\temp_ctd_processing\_input_files\sv20d0651')
    ctdp.run_process(server_path=r'C:\mw\temp_svea_server')

    # ctdp.create_setup_and_batch_files()
    # ctdp.run_seabird()
    # ctdp.modify_cnv_file()
    # ctdp.save_modified_ctd_file()
    # ctdp.move_raw_files()
    # ctdp.remove_files()
    server_path = r'\\\\scifi01\\scifi\\Processed\\mcseabirdchem'

    # # c.modify_cnv_file()
    # print(ctdp.paths)
    #
    # info = ctdp.cnv_info_object
    #
    # # cnv_file = r'C:\mw\temp_svea\cnv/SBE09_1387_20200508_0610_77_10_0383.cnv'
    # cnv_file = r'C:\mw\temp_svea\cnv/SBE09_1387_20200707_1013_77_10_0469.cnv'
    # cnv = cnv.CNVfile(cnv_file, ctdp)
    #
    # cnv2 = readCNV(cnv_file)
    #
    #
    # cnv.modify()
    #
    # save_path = cnv_file + 'v'
    # cnv.save_file(save_path)

