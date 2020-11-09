import codecs
import os
import logging
import logging.config
from pathlib import Path

import subprocess

from ctd_processing.read_ctd import readCNV
from ctd_processing import seabird
from ctd_processing import exceptions
from ctd_processing import cnv_column_info

try:
    from ctd_processing.stationnames_in_plot import insert_station_name
except:
    from stationnames_in_plot import insert_station_name



class CtdProcessing:
    def __init__(self, ctd_number=None, root_directory=None):

        self._surfacesoak = 'deep'

        # Directories
        self.paths = Paths(root_directory)
        self.cnv_column_info_directory = Path('cnv_column_info')

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

        self.setup_file_object = None
        self.batch_file_object = None

        self.ctd_number = ctd_number

        self.cnv_info_object = cnv_column_info.CnvInfoFiles(self.cnv_column_info_directory).get_info(self.ctd_number)

    @property
    def root_directory(self):
        return self.paths.root_directory
    
    @root_directory.setter
    def root_directory(self, directory):
        self.paths.root_directory = directory

    @property
    def ctd_number(self):
        return self._ctd_number

    @ctd_number.setter
    def ctd_number(self, number):
        if not number:
            return
        self._ctd_number = str(number)
        if self._ctd_number == '0817':
            self.ctd_config_suffix = '.CON'
        else:
            self.ctd_config_suffix = '.XMLCON'

    @property
    def surfacesoak_options(self):
        return self.setup_file_object.surfacesoak_options[:]

    @property
    def surfacesoak(self):
        return self._surfacesoak

    @surfacesoak.setter
    def surfacesoak(self, value):
        self._surfacesoak = value
        self.setup_file_object.surfacesoak = self._surfacesoak

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

    def load_seabird_files(self, file_path):
        # File path can be any seabird raw file. Even without suffix
        if not self.ctd_number:
            raise exceptions.InvalidInstrumentSerialNumber('No CTD number set')
        self.seabird_files = seabird.SeabirdFiles(file_path, self.ctd_number)
        self._save_info_from_seabird_files()

        self.setup_file_object = SetupFile(parent=self, surfacesoak=self.surfacesoak)
        self.batch_file_object = BatchFile(parent=self)

        # self.get_file()
        # self.load_options()
        # self.check_bl()
        # self.create_batch_file()
        # self.run_seabird()
        # self.modify_cnv_file()

    def create_batch_file(self):
        """
        Create a textfile that will be called by the bat-file.
        The file runs the SEB-programs
        """
        self.setup_file_object.create_file()
        self.batch_file_object.create_file()

    def run_seabird(self):
        self.batch_file_object.run_file()

    def _cnv_(self):
        pass

    def modify_cnv_file(self):
        # Read "down"-file
        cnv_down_file_path = self.setup_file_object.paths['cnv']
        self.ctd_data = readCNV(cnv_down_file_path)

        for index_str, info in self.cnv_info_object.items():
            index = info.index
            ok = info.ok
            text = info.parameter
            if 'true depth' in text.lower():
                pass


        # Här borde man kunna definiera sensor_index, dvs första kolumnen i self.cnv_column_info
        # den kommer automatiskt efter så som DatCnv.psa är inställd
        # Börjar med att kolla så det iaf är korrekt
        for sensor_row in self.cnv_column_info:
            sensor_index = sensor_row[0]
            sensor_text = sensor_row[2]
            if sensor_text == 'depFM: Depth [true depth, m], lat ':
                # kolla inte True Depth, det läggs till senare
                pass
            else:
                for ctd_header_row in self.ctd_data[1]:
                    if sensor_text in ctd_header_row:
                        sensor_index_cnv_header = int(ctd_header_row[7:9])
                        break
                    else:
                        sensor_index_cnv_header = 'not found'

                if sensor_index == sensor_index_cnv_header:
                    pass

                else:
                    print(
                        'WARNING!!! sensor column index in self.cnv_column_info (%s) is not the same as in the cnv header (%s), stopping script!!!' % (
                        sensor_index, sensor_index_cnv_header))
                    print
                    'FIX THIS NOW!!!'
                    print
                    sensor_index_cnv_header
                    print
                    sensor_text
                    smurf

        sh = [];
        for rows in self.ctd_data[1]:
            sh.append(split(':\s', str.rstrip(rows)).pop())

        # get rid of the last column of sh (flags)
        sh.pop()

        # Extract the pressure, sigmaT and FW depth:
        # depFM: Depth [fresh water, m], lat = 0
        for cols in self.ctd_data[1]:
            if 'prDM: Pressure, Digiquartz [db]' in cols:
                col_pres = int(cols[7:9])
            if 'sigma-t00: Density [sigma-t' in cols:
                col_dens = int(cols[7:9])
            if 'sigma-t11: Density, 2 [sigma-t' in cols:
                col_dens2 = int(cols[7:9])
            if 'depFM: Depth [fresh water, m]' in cols:
                col_depth = int(cols[7:9])
            if 'svCM: Sound Velocity [Chen-Millero, m/s]' in cols:
                col_sv = int(cols[7:9])

        prdM = [row[col_pres] for row in self.ctd_data[2]]

        if self.cnv_column_info[col_dens][3] == 1:
            sigT = [row[col_dens] for row in self.ctd_data[2]]
        elif self.cnv_column_info[col_dens2][3] == 1:  # use secondary sigT
            sigT = [row[col_dens2] for row in self.ctd_data[2]]
        else:
            sigT = [-9.990e-29 for i in range(len(self.ctd_data[2]))]

        depFM = [row[col_depth] for row in self.ctd_data[2]]
        svCM = [row[col_sv] for row in self.ctd_data[2]]

        # Beräkning från Arnes CTrueDepth.bas program
        # ' Plockar pressure från cnv-filen
        #        dblPres = Mid$(strDataline, ((strPresWhere * 11) + 1), 11)
        # ' decibar till bar
        #        dblRPres = dblPres * 10
        # ' Plockar sigmaT från cnv-filen
        #        dblSig = Mid$(strDataline, ((strSigmaTWhere * 11) + 1), 11)
        # ' Beräknar densitet
        #        dblDens = (dblSig + 1000) / 1000#
        # ' Beräknar delta djup
        #        dblDDjup = (dblRPres - dblP0) / (dblDens * dblg)
        # ' Summerar alla djup och använd framräknande trycket i nästa iteration
        #        dblDepth = dblDepth + dblDDjup
        #        dblP0 = dblRPres

        # Beräkning av truedepth #Ersätt depFM med true depth i headern
        # Start params
        g = 9.818  # ' g vid 60 gr nord (dblg)
        P0 = 0  # ' starttrycket (vid ytan) (dblP0)
        Dens0 = (sigT[0] + 1000.) / 1000.  # ' start densitet
        Depth = 0  # ' start summadjup (dblDepth)
        # Nya variabler
        RPres = []
        Dens = []
        DDepth = []
        TrueDepth = []

        for q in range(0, len(prdM)):

            if sigT[q] != -9.990e-29:
                # decibar till bar (dblRPres)
                RPres = prdM[q] * 10.
                # Beräknar densitet (dblDens)
                Dens = (sigT[q] + 1000.) / 1000.
                # Beräknar delta djup (dblDDjup)
                DDepth = (RPres - P0) / ((Dens + Dens0) / 2. * g)
                # Summerar alla djup och använd framräknande trycket i nästa loop
                # Om det är första (ej helt relevant kanske) eller sista värdet dela med två enl. trappetsmetoden
                Dens0 = Dens
                #    if q == 0 or q == (len(prdM)-1):
                #        Depth = Depth + DDepth / 2.
                #    else:
                #        Depth = Depth + DDepth
                # Ändrad av Örjan 2015-02-10 /2. första och sista djupet borttaget.
                Depth = Depth + DDepth
                # Spara framräknat djup för nästa loop
                P0 = RPres
                # Sparar undan TrueDepth
                TrueDepth.append(Depth)
            else:
                TrueDepth.append(-9.990e-29)

        # Header
        # Lägg till tid för true depth beräkning i header & average sound velocity
        # xx = [i for i,x in enumerate(self.ctd_data[0]) if x == '** Primary sensors\n']
        xx = [i for i, x in enumerate(self.ctd_data[0]) if '** Ship' in x]
        print
        xx
        tid = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        svMean = sum(svCM) / len(svCM)
        self.ctd_data[0].insert(xx[0] + 1, '** Average sound velocity: ' + str('%6.2f' % svMean) + ' m/s\n')
        self.ctd_data[0].insert(xx[0] + 2, '** True-depth calculation ' + tid + '\n')
        self.ctd_data[0].insert(xx[0] + 3, '** CTD Python Module SMHI /ver 3-12/ feb 2012 \n')
        # self.ctd_data[0].insert(xx[0]+4,'** LIMS Job: 20' + self.year + self.cnty + self.ship + '-' + self.serie + '_SYNC\n')
        self.ctd_data[0].insert(xx[0] + 4,
                                '** LIMS Job: 20' + self.year + self.cnty + self.ship + '-' + self.serie + '\n')

        # Ersätter depFM: Depth [fresh water, m], lat = 0
        # med depFM: Depth [true depth, m], lat = 0
        # xx = [i for i,x in enumerate(self.ctd_data[0]) if 'depFM: Depth [fresh water, m]' in x]
        # xx = [i for i,x in enumerate(self.ctd_data[0]) if x == '# name 21 = depFM: Depth [fresh water, m], lat = 0\n']
        # self.ctd_data[0][xx[0]] = self.ctd_data[0][xx[0]].replace('fresh water','true depth')

        index_true_depth = '99'

        for i, x in enumerate(self.ctd_data[0]):

            # Lägger till enhet till PAR/Irradiance

            if 'par: PAR/Irradiance' in x:
                self.ctd_data[0][i] = self.ctd_data[0][i][:-2] + ' [µE/(cm^2*s)]\n'
            # Lägger till Chl-a på de fluorometrar som har beteckning som börjar på FLNTURT
            if 'Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]' in x:
                Fluo_index = i
            if 'Fluorometer, WET Labs ECO-AFL/FL -->' in x and '<SerialNumber>FLNTURT' in self.ctd_data[0][i + 2]:
                self.ctd_data[0][i] = self.ctd_data[0][i].replace('Fluorometer', 'Chl-a Fluorometer')
                self.ctd_data[0][Fluo_index] = self.ctd_data[0][Fluo_index].replace('Fluorescence',
                                                                                    'Chl-a Fluorescence')
                # Lägger till Phycocyanin på den fluorometer som har serialnumber som börjar på FLPCRTD
            if 'Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]' in x:
                Fluo_index_2 = i
            if 'Fluorometer, WET Labs ECO-AFL/FL, 2 -->' in x and '<SerialNumber>FLPCRTD' in self.ctd_data[0][
                i + 2]:
                self.ctd_data[0][i] = self.ctd_data[0][i].replace('Fluorometer', 'Phycocyanin Fluorometer')
                self.ctd_data[0][Fluo_index_2] = self.ctd_data[0][Fluo_index_2].replace('Fluorescence',
                                                                                        'Phycocyanin Fluorescence')
            if 'depFM: Depth [fresh water, m]' in x:
                self.ctd_data[0][i] = self.ctd_data[0][i].replace('fresh water', 'true depth')
                index_true_depth = x[7:9].strip()
            if '# span ' + index_true_depth + ' =' in x:
                if int(index_true_depth) < 10:
                    self.ctd_data[0][i] = ('# span %s =%11.3f,%11.3f%7s\n' % (
                    index_true_depth, min(TrueDepth), max(TrueDepth), ''))
                else:
                    self.ctd_data[0][i] = ('# span %s =%11.3f,%11.3f%6s\n' % (
                    index_true_depth, min(TrueDepth), max(TrueDepth), ''))

        # Ersätt data i fresh water kolumnen med true depth avrundar true depth till tre decimaler
        for row in range(0, len(prdM)):
            if TrueDepth[row] == -9.990e-29:
                self.ctd_data[2][row][col_depth] = -9.990e-29
            else:
                self.ctd_data[2][row][col_depth] = round(TrueDepth[row], 3)

        # justera span för de parametrar som har sensor_flag = 0
        for sensor_row in self.cnv_column_info:
            if sensor_row[-1] == 0:  # entire sensro marked as bad, set span to -9.990e-29, -9.990e-29
                sensor_text = sensor_row[2]
                index_sensor = '99'
                for i, x in enumerate(self.ctd_data[0]):
                    if sensor_text in x:
                        index_sensor = x[7:9].strip()
                    if '# span ' + index_sensor + ' =' in x:
                        if int(index_sensor) < 10:
                            self.ctd_data[0][i] = ('# span %s = -9.990e-29, -9.990e-29%7s\n' % (index_sensor, ''))
                        else:
                            self.ctd_data[0][i] = ('# span %s = -9.990e-29, -9.990e-29%6s\n' % (index_sensor, ''))

        # TODO: Lägg till if sats som skapar kataloger vid nytt år. /MHAN
        if not os.path.exists(self.data_directory + '20' + self.year + '\\'):  # hoppas denna funkar /OBac
            os.mkdir(self.data_directory + '20' + self.year + '\\')

        filelist = os.walk(self.data_directory + '20' + self.year + '\\').next()[2]

        # print filelist
        # print self.data_directory +'20' + self.year + '\\'

        if not self.new_fname + '.cnv' in filelist:
            # Skriver tillbaka header self.ctd_data[0],
            test_file = open(self.data_directory + '20' + self.year + '\\' + self.new_fname + '.cnv', 'w')
            test_file.writelines(self.ctd_data[0])
            test_file.close()

            # och lägger tillbaka data self.ctd_data[2] till samma fil
            test_file = open(self.data_directory + '20' + self.year + '\\' + self.new_fname + '.cnv', "a")
            for row in self.ctd_data[2]:
                row_to_write, bad_flag = self.get_string_for_data_file(row)

                if bad_flag:
                    print
                    'Bad flag detected at %s db, in %s' % (row[1], self.new_fname)
                # else: # can activate this to not write this depth to the data file
                test_file.write(row_to_write)
                test_file.write('\n')
            test_file.close()

            # TODO: copy cnv and plots to file server
            # C:\ctd\plots\\' + '20' + self.year + ' /f' + self.new_fname
            # /a_' + self.stationname
            # /a_TS_diff_' + self.stationname
            # /a_oxygen_diff_' + self.stationname
            # /a_fluor_turb_par_' + self.stationname

            #            if os.path.exists(self.shark_file_directory):
            #                self.write_shark_file(self.shark_file_directory)
            #
            #            else: #Om det saknas nätverk läggs filen lokalt.
            #                self.write_shark_file(self.shark_file_directory_lokal)
            #                print 'Network is missing...'
            #                print 'SHARK import file are available here %s' % self.shark_file_directory_lokal
            #
            # Rensa och flytta filer
            # os.remove('C:\\ctd\\temp\\u' + new_fname + '.cnv')
            os.remove(self.working_directory + 'd' + self.new_fname + '.cnv')
            os.remove(self.working_directory + self.new_fname + '.cnv')

            shutil.move(self.working_directory + 'u' + self.new_fname + '.cnv',
                        self.data_directory + '20' + self.year + '\\up_cast')
            shutil.move(self.working_directory + self.new_fname + self.ctdconfig,
                        self.raw_files_directory + '20' + self.year)
            shutil.move(self.working_directory + self.new_fname + '.hex',
                        self.raw_files_directory + '20' + self.year)
            shutil.move(self.working_directory + self.new_fname + '.hdr',
                        self.raw_files_directory + '20' + self.year)
            shutil.move(self.working_directory + self.new_fname + '.bl',
                        self.raw_files_directory + '20' + self.year)
            try:
                shutil.move(self.working_directory + self.new_fname + '.btl',
                            self.raw_files_directory + '20' + self.year)
            except:
                print('No .btl file to move')
            try:
                shutil.move(self.working_directory + self.new_fname + '.ros',
                            self.raw_files_directory + '20' + self.year)
            except:
                print('No .ros file to move')


        else:  # filen finns redan

            q = raw_input('Files do already exist. Overwrite? Y or N?')
            # q = 'Y'
            if q.upper() == 'Y':  # om Y; skriv över filen
                # Skriver tillbaka header self.ctd_data[0],
                test_file = open(self.data_directory + '20' + self.year + '\\' + self.new_fname + '.cnv', 'w')
                test_file.writelines(self.ctd_data[0])
                test_file.close()

                # och lägger tillbaka data self.ctd_data[2] till samma fil
                test_file = open(self.data_directory + '20' + self.year + '\\' + self.new_fname + '.cnv', "a")
                for row in self.ctd_data[2]:
                    row_to_write, bad_flag = self.get_string_for_data_file(row)

                    if bad_flag:
                        print
                        'Bad flag detected at %s db, in %s' % (row[1], self.new_fname)
                    # else: # can activate this to not write this depth to the data file
                    test_file.write(row_to_write)
                    test_file.write('\n')

                test_file.close()

                # TODO:
                # TODO: copy cnv and plots to file server
                # C:\ctd\plots\\' + '20' + self.year + ' /f' + self.new_fname
                # /a_' + self.stationname
                # /a_TS_diff_' + self.stationname
                # /a_oxygen_diff_' + self.stationname
                # /a_fluor_turb_par_' + self.stationname

                # Rensa och flytta filer
                # os.remove('C:\\ctd\\temp\\u' + new_fname + '.cnv')
                os.remove(self.working_directory + 'd' + self.new_fname + '.cnv')
                os.remove(self.working_directory + self.new_fname + '.cnv')

                # ta bort äldre filer och kopiera över det nya
                try:
                    os.remove(self.data_directory + '20' + self.year + '\\up_cast\\u' + self.new_fname + '.cnv')
                except:
                    print('No old up_cast file to delete')
                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' + self.new_fname + self.ctdconfig)
                except:
                    pass

                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' + self.new_fname + '.hex')
                except:
                    pass

                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' + self.new_fname + '.hdr')
                except:
                    pass

                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' + self.new_fname + '.bl')
                except:
                    pass

                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' + self.new_fname + '.btl')
                except:
                    print('No old .btl file to delete')
                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' + self.new_fname + '.ros')
                except:
                    print('No old .ros file to delete')

                print
                'work', self.working_directory + 'u' + self.new_fname + '.cnv'
                print
                'data', self.data_directory + '20' + self.year + '\\up_cast'

                # TODO
                # copy up-cast
                shutil.move(self.working_directory + 'u' + self.new_fname + '.cnv',
                            self.data_directory + '20' + self.year + '\\up_cast')
                shutil.move(self.working_directory + self.new_fname + self.ctdconfig,
                            self.raw_files_directory + '20' + self.year)
                shutil.move(self.working_directory + self.new_fname + '.hex',
                            self.raw_files_directory + '20' + self.year)
                shutil.move(self.working_directory + self.new_fname + '.hdr',
                            self.raw_files_directory + '20' + self.year)
                shutil.move(self.working_directory + self.new_fname + '.bl',
                            self.raw_files_directory + '20' + self.year)
                try:
                    shutil.move(self.working_directory + self.new_fname + '.btl',
                                self.raw_files_directory + '20' + self.year)
                except:
                    print('No .btl file to move')
                try:
                    shutil.move(self.working_directory + self.new_fname + '.ros',
                                self.raw_files_directory + '20' + self.year)
                except:
                    print('No .ros file to move')


class Paths:
    def __init__(self, root_directory=None):

        self.directories = {}
        self.files = {}

        for d in ['root', 'working', 'setup', 'data', 'raw_files', 'plot']:
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
        self.directories['data'] = Path(root, 'data')
        self.directories['raw_files'] = Path(root, 'raw_files')
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
        return self.directories.get(dir_id)


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
        subprocess.run(self.batch_file_path)


class SetupFile:
    def __init__(self,
                 parent,
                 surfacesoak=None,
                 **kwargs):

        self.parent = parent

        self._save_variables()

        self.surfacesoak_options = ['deep', 'manual', '0.3', '0.5']
        self._surfacesoak = None
        if surfacesoak:
            self.surfacesoak = surfacesoak

        self.paths = {}

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
        value = str(value)
        if value not in self.surfacesoak_options:
            raise exceptions.InvalidSurfacesoak
        self._surfacesoak = value

    def _set_paths(self):

        self.paths['ctd_config'] = Path(self.working_directory, self.new_file_stem + self.ctd_config_suffix)
        self.paths['hex'] = Path(self.working_directory, f'{self.new_file_stem}.hex')
        self.paths['ros'] = Path(self.working_directory, f'{self.new_file_stem}.ros')
        self.paths['cnv'] = Path(self.working_directory, f'd{self.new_file_stem}.cnv')

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
        if not self.surfacesoak:
            raise exceptions.InvalidSurfacesoak('Surfacesoak not set!')

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
        self.lines['plot1'] = f'seaplot /p{self.paths["psa_plot1"]} /i{cnv_file_path} /a_{self.station_name} /o{self.plot_directory}{self.year} /f{self.new_file_stem}'
        self.lines['plot2'] = f'seaplot /p{self.paths["psa_plot2"]} /i{cnv_file_path} /a_TS_diff_{self.station_name} /o{self.plot_directory}{self.year} /f{self.new_file_stem}'
        self.lines['plot3'] = f'seaplot /p{self.paths["psa_plot3"]} /i{cnv_file_path} /a_oxygen_diff_{self.station_name} /o{self.plot_directory}{self.year} /f{self.new_file_stem}'
        self.lines['plot4'] = f'seaplot /p{self.paths["psa_plot4"]} /i{cnv_file_path} /a_fluor_turb_par_{self.station_name} /o{self.plot_directory}{self.year} /f{self.new_file_stem}'

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


def get_logger(existing_logger=None):
    if not os.path.exists('log'):
        os.makedirs('log')
    if existing_logger:
        return existing_logger
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('timedrotating')
    return logger


if __name__ == '__main__':
    c = CtdProcessing(root_directory=r'C:\mw\temp_ctd_processing', ctd_number=1387)
    c.load_seabird_files(r'C:\mw\data\sbe_raw_files\SBE09_1387_20200816_1055_77_10_0496')
    print(c.paths)

    cnv_file = r'C:\mw\temp_svea\cnv/SBE09_1387_20200508_0610_77_10_0383.cnv'
    cnv = readCNV(cnv_file)

