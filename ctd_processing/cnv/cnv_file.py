import time
import os
import pathlib
import datetime

from ctd_processing import cnv_column_info
from ctd_processing import exceptions

from ctd_processing.cnv.cnv_header import CNVheader
from ctd_processing.cnv.cnv_parameter import CNVparameter


class CNVfile:
    def __init__(self, ctd_files=None, cnv_column_info_directory=None, use_cnv_info_format=False, **kwargs):
        self._ctd_files = ctd_files
        key = 'cnv_down'
        self.file_path = self._ctd_files(key)
        if not self.file_path:
            raise FileNotFoundError(key)
        if not self.file_path.exists():
            raise FileNotFoundError(self.file_path)

        self.instrument_number = self._ctd_files.instrument_number
        cnv_info_files = cnv_column_info.CnvInfoFiles(cnv_column_info_directory)
        self.cnv_info_object = cnv_info_files.get_info(self.instrument_number)
        self.use_cnv_info_format = use_cnv_info_format

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

        self.date_format_in_file = '%b %d %Y %H:%M:%S'
        self._time = None
        self._lat = None
        self._lon = None
        self._station = None

    @property
    def time(self):
        return self._time

    @property
    def lat(self):
        return self._lat

    @property
    def lon(self):
        return self._lon

    @property
    def station(self):
        return self._station

    def modify(self):
        self._check_index()
        self._modify_header_information()
        self._modify_irradiance()
        self._modify_fluorescence()
        self._modify_depth()

    def save_file(self, file_path, overwrite=False):
        file_path = pathlib.Path(file_path)
        if file_path.exists() and not overwrite:
            raise FileExistsError(file_path)
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

    # def _save_instrument_files_info(self):
    #         self.year = self._ctd_files.year
    #         self.ctry = self._ctd_files.ctry
    #         self.ship = self._ctd_files.ship
    #         self.serie = self._ctd_files.serial_number

    def _load_info(self):
        header = True
        has_set_value_length = False
        self.nr_data_lines = 0
        with open(self.file_path) as fid:
            for r, line in enumerate(fid):
                strip_line = line.strip()
                if '* System UTC' in line:
                    self._time = datetime.datetime.strptime(line.split('=')[1].strip(), self.date_format_in_file)
                if '* NMEA Latitude' in line:
                    self._lat = line.split('=')[1].strip()[:-1].replace(' ', '')
                if '* NMEA Longitude' in line:
                    self._lon = line.split('=')[1].strip()[:-1].replace(' ', '')
                if line.startswith('** Station'):
                    self._station = line.split(':')[-1].strip()

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
        now = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        after_str = '** Ship'
        rows_to_insert = [f'** Average sound velocity: {str("%6.2f" % svMean)} m/s',
                          f'** True-depth calculation {now}',
                          # f'** CTD Python Module SMHI /ver 3-12/ feb 2012',
                          # f'** Python Module: ctd_processing, nov 2020'
                          # f'** LIMS Job: {self.year}{self.ctry}{self.ship}-{self.serie}'
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