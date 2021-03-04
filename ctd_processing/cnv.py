import os
from pathlib import Path
from time import gmtime, strftime
from ctd_processing import exceptions
from ctd_processing import utils


class CNVparameter:
    def __init__(self, use_cnv_info_format=False, cnv_info_object=None, **data):
        self.info = {}
        for key, value in data.items():
            if key in ['index']:
                value = int(value)
            self.info[key] = value
            setattr(self, key, value)

        self.use_cnv_info_format = use_cnv_info_format
        self.cnv_info_object = cnv_info_object
        self._tot_value_length = 11
        self._value_format = 'd'
        self._nr_decimals = None
        self.sample_value = None
        self._data = []
        self.active = False

    def __repr__(self):
        return_list = [f'CNVparameter (dict): {self.info["name"]}']
        blanks = ' '*4
        for key, value in self.info.items():
            return_list.append(f'{blanks}{key:<20}{value}')

        if len(self._data):
            return_list.append(f'{blanks}{"Sample value":<20}{self.sample_value}')
            if self.use_cnv_info_format:
                form = f'{self.format} (from info file)'
            else:
                form = f'{self.format} (calculated from data)'
            return_list.append(f'{blanks}{"Value format":<20}{form}')
        return '\n'.join(return_list)

    def _set_nr_decimals(self, value_str):
        # Keeps the highest number och decimals in self._nr_decimals
        # Also saves sample_value
        if self._nr_decimals is None:
            self._nr_decimals = len(value_str.strip().split('e')[0].split('.')[-1])
            self.sample_value = float(value_str)
        else:
            nr = len(value_str.strip().split('e')[0].split('.')[-1])
            if nr > self._nr_decimals:
                self._nr_decimals = nr
                self.sample_value = float(value_str)

    @property
    def format(self):
        if self.use_cnv_info_format:
            return self.cnv_info_object.format
        if self._nr_decimals is None:
            form = f'{self._tot_value_length}{self._value_format}'
        else:
            form = f'{self._tot_value_length}.{self._nr_decimals}{self._value_format}'
        return form

    def set_value_length(self, length):
        self._tot_value_length = length

    def add_data(self, value_str):
        string = value_str.strip('+-')
        if '+' in string or '-' in string:
            self._value_format = 'e'
        elif '.' in value_str:
            self._value_format = 'f'
        if '.' in value_str:
            self._set_nr_decimals(value_str)
            value = float(value_str)
        else:
            value = int(value_str)
            self._value_format = 'd'

        self._data.append(value)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def change_name(self, new_name):
        self.info['name'] = new_name
        self.name = new_name

    def get_value_as_string_for_index(self, index):
        return '{:{}}'.format(self.data[index], self.format)

    def set_active(self, is_active):
        self.active = is_active


class CNVheader:
    def __init__(self, linebreak='\n'):
        self.linebreak = linebreak
        self.rows = []

    def add_row(self, row):
        self.rows.append(row.strip())

    def insert_row_after(self, row, after_str, ignore_if_string=None):
        for line in self.rows:
            if row == line:
                return
        for i, value in enumerate(self.rows[:]):
            if after_str in value:
                if ignore_if_string:
                    if ignore_if_string in self.rows[i+1]:
                        continue
                self.rows.insert(i+1, row.strip())
                break

    def append_to_row(self, string_in_row, append_string):
        for i, value in enumerate(self.rows[:]):
            if string_in_row in value:
                new_string = self.rows[i] + append_string.rstrip()
                if self.rows[i] == new_string:
                    continue
                self.rows[i] = new_string
                break

    def get_row_index_for_matching_string(self, match_string, as_list=False):
        index = []
        for i, value in enumerate(self.rows):
            if match_string in value:
                index.append(i)
        if not index:
            return None
        if as_list:
            return index
        if len(index) == 1:
            return index[0]
        return index

    def replace_string_at_index(self, index, from_string, to_string, ignore_if_present=True):
        if index is None:
            return
        if type(index) == int:
            index = [index]
        for i in index:
            if to_string in self.rows[i] and ignore_if_present:
                continue
            self.rows[i] = self.rows[i].replace(from_string, to_string)

    def replace_row(self, index, new_value):
        self.rows[index] = new_value.strip()


class CNVfile:
    def __init__(self, file_path, ctd_processing_object=None, **kwargs):
        self.file_path = Path(file_path)
        self.ctd_processing_object = ctd_processing_object
        self.cnv_info_object = self.ctd_processing_object.cnv_info_object
        self.use_cnv_info_format = self.ctd_processing_object.use_cnv_info_format
        self._load_ctd_processing_object_info()

        self.parameters = {}
        self.header = CNVheader()
        self.data = {}
        self.nr_data_lines = None
        self.linebreak = kwargs.get('linebreak', '\n')

        self.missing_value = -9.990e-29
        self.missing_value_str = '-9.990e-29'
        self.g = 9.818  # g vid 60 gr nord (dblg)

        self._load_info()
        self._save_columns()
        self._set_active_parameters()

    def modify(self):
        self._check_index()
        self._modify_header_information()
        self._modify_irradiance()
        self._modify_fluorescence()
        self._modify_depth()

    def save_file(self, file_path, overwrite=False):
        file_path = Path(file_path)
        if file_path.exists() and not overwrite:
            raise exceptions.FileExists(file_path)
        if not file_path.parent.exists():
            os.makedirs(file_path.parent)
        all_rows = []
        all_rows.extend(self.header.rows)
        all_rows.extend(self._get_data_rows())
        all_rows.append('')
        with open(file_path, 'w') as fid:
            fid.write(self.linebreak.join(all_rows))

    def _get_data_rows(self):
        data_rows = []
        for r in range(self.nr_data_lines):
            line_list = []
            for par, obj in self.parameters.items():
                value = obj.get_value_as_string_for_index(r)
                line_list.append(value)
            line_string = ''.join(line_list)
            data_rows.append(line_string)
        return data_rows

    def _load_ctd_processing_object_info(self):
        if self.ctd_processing_object:
            self.cnv_info_object = self.ctd_processing_object.cnv_info_object
            self.year = self.ctd_processing_object.year
            self.ctry = self.ctd_processing_object.ctry
            self.ship = self.ctd_processing_object.ship
            self.serie = self.ctd_processing_object.serial_number

    def _load_info(self):
        header = True
        has_set_value_length = False
        self.nr_data_lines = 0
        with open(self.file_path) as fid:
            for r, line in enumerate(fid):
                strip_line = line.strip()
                if '*END*' in line:
                    self.header.add_row(line)
                    header = False
                    continue
                if strip_line.startswith('# name'):
                    name, par = [item.strip() for item in strip_line.split('=', 1)]
                    index = name.split(' ')[-1]
                    obj = CNVparameter(use_cnv_info_format=self.use_cnv_info_format,
                                       cnv_info_object=self.cnv_info_object[int(index)],
                                       index=index, name=par)
                    self.parameters[obj.index] = obj
                if header:
                    self.header.add_row(line)
                else:
                    if not line.strip():
                        continue
                    self.nr_data_lines += 1
                    split_line = strip_line.split()
                    if not has_set_value_length:
                        tot_len = len(line.rstrip())
                        value_length = tot_len / len(split_line)
                        int_value_lenght = int(value_length)
                        if int_value_lenght != value_length:
                            raise ValueError('Something is wrong in the file!')
                        for i, value in enumerate(split_line):
                            self.parameters[i].set_value_length(int_value_lenght)
                        has_set_value_length = True
                    for i, value in enumerate(split_line):
                        self.parameters[i].add_data(value)

    def _save_columns(self):
        self.col_pres = None
        self.col_dens = None
        self.col_dens2 = None
        self.col_depth = None
        self.col_sv = None

        for par in self.parameters.values():
            if 'prDM: Pressure, Digiquartz [db]' in par.name:
                self.col_pres = par.index
            elif 'sigma-t00: Density [sigma-t' in par.name:
                self.col_dens = par.index
            elif 'sigma-t11: Density, 2 [sigma-t' in par.name:
                self.col_dens2 = par.index
            elif 'depFM: Depth [fresh water, m]' in par.name:
                self.col_depth = par.index
            elif 'depFM: Depth [true depth, m]' in par.name:
                self.col_depth = par.index
            elif 'svCM: Sound Velocity [Chen-Millero, m/s]' in par.name:
                self.col_sv = par.index

    def _set_active_parameters(self):
        for i, info in self.cnv_info_object.items():
            self.parameters[i].set_active(info.active)

    def _change_parameter_name(self, current_name, new_name):
        for par in self.parameters.values():
            if par.name == new_name:
                return
        for par in self.parameters.values():
            if current_name == par.name:
                par.change_name(new_name)

    def _get_parameter_name_matching_string(self, match_string):
        for par in self.parameters.values():
            if match_string in par.name:
                return par.name

    def _check_index(self):
        if not self.cnv_info_object:
            raise exceptions.MissingAttribute('cnv_info_object')
        for info, cnv in zip(self.cnv_info_object.values(), self.parameters.values()):
            if 'depFM: Depth [true depth, m], lat' in info.name:
                continue
            if info.name not in cnv.name:
                print(info.name)
                print(cnv.name)
                raise exceptions.InvalidParameterIndex(f'Index stämmer inte i cnv för parameter: {info.name}')
            cnv.active = True

        # Här borde man kunna definiera sensor_index, dvs första kolumnen i self.cnv_column_info
        # den kommer automatiskt efter så som DatCnv.psa är inställd
        # Börjar med att kolla så det iaf är korrekt

    def _get_pressure_data(self):
        return self.parameters[self.col_pres].data

    def _get_depth_data(self):
        return self.parameters[self.col_depth].data

    def _get_sound_velocity_data(self):
        return self.parameters[self.col_sv].data

    def _get_density_data(self):
        if self.parameters[self.col_dens].active:
            return self.parameters[self.col_dens].data
        elif self.parameters[self.col_dens2].active:
            return self.parameters[self.col_dens2].data
        else:
            return [self.missing_value]*self.nr_data_lines

    def _get_calculated_true_depth(self):
        prdM_data = self._get_pressure_data()
        sigT_data = self._get_density_data()

        # Beräkning av truedepth # Ersätt depFM med true depth i headern
        # Start params
        dens_0 = (sigT_data[0] + 1000.) / 1000.  # ' start densitet
        p_0 = 0
        depth = 0
        true_depth = []
        for q in range(len(prdM_data)):
            if sigT_data[q] != self.missing_value:
                # decibar till bar (dblRPres)
                rpres = prdM_data[q] * 10.
                # Beräknar densitet (dblDens)
                dens = (sigT_data[q] + 1000.) / 1000.
                # Beräknar delta djup (dblDDjup)
                ddepth = (rpres - p_0) / ((dens + dens_0) / 2. * self.g)
                # Summerar alla djup och använd framräknande trycket i nästa loop
                # Om det är första (ej helt relevant kanske) eller sista värdet dela med två enl. trappetsmetoden
                dens_0 = dens
                #    if q == 0 or q == (len(prdM)-1):
                #        Depth = Depth + DDepth / 2.
                #    else:
                #        Depth = Depth + DDepth
                # Ändrad av Örjan 2015-02-10 /2. första och sista djupet borttaget.
                depth = depth + ddepth
                # Spara framräknat djup för nästa loop
                p_0 = rpres
                # Sparar undan TrueDepth
                true_depth.append(depth)
            else:
                true_depth.append(self.missing_value)
        return true_depth

    def _get_mean_sound_velocity(self):
        svCM_data = self._get_sound_velocity_data()
        return sum(svCM_data) / len(svCM_data)

    def _modify_header_information(self):
        svMean = self._get_mean_sound_velocity()
        now = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        after_str = '** Ship'
        rows_to_insert = [f'** Average sound velocity: {str("%6.2f" % svMean)} m/s',
                          f'** True-depth calculation {now}',
                          # f'** CTD Python Module SMHI /ver 3-12/ feb 2012',
                          f'** Python Module: ctd_processing, nov 2020',
                          f'** LIMS Job: {self.year}{self.ctry}{self.ship}-{self.serie}'
        ]
        for row in rows_to_insert:
            if 'True-depth calculation' in row:
                self.header.insert_row_after(row, after_str, ignore_if_string='True-depth calculation')
            else:
                self.header.insert_row_after(row, after_str)
            after_str = row

    def _modify_irradiance(self):
        self.header.append_to_row('par: PAR/Irradiance', ' [µE/(cm^2*s)]')

    def _modify_fluorescence(self):
        # Lägger till Chl-a på de fluorometrar som har beteckning som börjar på FLNTURT
        par_name_1 = self._get_parameter_name_matching_string('Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]')
        fluo_index_1 = self.header.get_row_index_for_matching_string('Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]')
        fluo_xml_index_1 = self.header.get_row_index_for_matching_string('Fluorometer, WET Labs ECO-AFL/FL -->')
        serial_index_1 = self.header.get_row_index_for_matching_string('<SerialNumber>FLNTURT', as_list=True)

        par_name_2 = self._get_parameter_name_matching_string('Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]')
        fluo_index_2 = self.header.get_row_index_for_matching_string('Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]')
        fluo_xml_index_2 = self.header.get_row_index_for_matching_string('Fluorometer, WET Labs ECO-AFL/FL, 2 -->')
        serial_index_2 = self.header.get_row_index_for_matching_string('<SerialNumber>FLPCRTD', as_list=True)

        if fluo_xml_index_1 and (fluo_xml_index_1 + 2) in serial_index_1:
            self.header.replace_string_at_index(fluo_xml_index_1, 'Fluorometer', 'Chl-a Fluorometer')
            self.header.replace_string_at_index(fluo_index_1, 'Fluorescence', 'Chl-a Fluorescence')
            new_par_name_1 = par_name_1.replace('Fluorescence', 'Chl-a Fluorescence')
            self._change_parameter_name(par_name_1, new_par_name_1)

        if fluo_xml_index_2 and (fluo_xml_index_2 + 2) in serial_index_2:
            self.header.replace_string_at_index(fluo_xml_index_2, 'Fluorometer', 'Phycocyanin Fluorometer')
            self.header.replace_string_at_index(fluo_index_2, 'Fluorescence', 'Phycocyanin Fluorescence')
            new_par_name_2 = par_name_2.replace('Fluorescence', 'Phycocyanin Fluorescence')
            self._change_parameter_name(par_name_2, new_par_name_2)

    def _modify_depth(self):
        index = self.header.get_row_index_for_matching_string('depFM: Depth [fresh water, m]')
        self.header.replace_string_at_index(index, 'fresh water', 'true depth')
        par_name = self._get_parameter_name_matching_string('depFM: Depth [fresh water, m]')
        if par_name:
            new_par_name = par_name.replace('fresh water', 'true depth')
            self._change_parameter_name(par_name, new_par_name)

        span_depth_index = self.header.get_row_index_for_matching_string(f'# span {self.col_depth}')
        true_depth_values = self._get_calculated_true_depth()
        if int(self.col_depth) < 10:
            new_line = '# span %s =%11.3f,%11.3f%7s' % (self.col_depth, min(true_depth_values), max(true_depth_values), '')
        else:
            new_line = '# span %s =%11.3f,%11.3f%6s' % (self.col_depth, min(true_depth_values), max(true_depth_values), '')
        self.header.replace_row(span_depth_index, new_line)

        # Ersätt data i fresh water kolumnen med true depth avrundar true depth till tre decimaler
        new_depth_data = []
        for value in true_depth_values:
            if value == self.missing_value:
                new_depth_data.append(self.missing_value_str)
            else:
                new_depth_data.append(round(value, 3))
        self.parameters[self.col_depth].data = new_depth_data

    def _modify_span(self):
        # Justera span för de parametrar som har flaggats som bad
        for index, info in self.cnv_info_object.items():
            if info.active:
                continue
            span_index = self.header.get_row_index_for_matching_string(f'# span {info.index}')
            if int(info.index) < 10:
                new_line = f'# span {span_index} = {self.missing_value_str}, {self.missing_value_str}{" ": >7}'
            else:
                new_line = f'# span {span_index} = {self.missing_value_str}, {self.missing_value_str}{" ": >6}'
            self.header.replace_row(span_index, new_line)


if __name__ == '__main__':
    cnv_file = r'C:\mw\temp_svea\cnv/SBE09_1387_20200508_0610_77_10_0383.cnv'
    cnv = CNVfile(cnv_file, None)
    print(cnv.parameters[3])