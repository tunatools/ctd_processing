from pathlib import Path

import xml.etree.ElementTree as ET

from ctd_processing import utils


class PSAfile:
    """
    psa-files are configuration files used for seabird processing.
    """
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.tree = ET.parse(self.file_path)

    def _has_condition(self, element, tag_list, condition):
        for tag in tag_list:
            element = element.find(tag)
        key, value = [item.strip() for item in condition.split('==')]
        v = element.get(key)
        if element.get(key) == value:
            return True

    def _get_element_from_tag_list(self, tag_list):
        element = self.tree
        for tag in tag_list:
            if '{{' in tag:
                condition_found = False
                tag, condition = tag.split('{{')
                condition = condition.strip('}}')
                condition_tag_list = [item.strip() for item in condition.split(';')]
                key_value = condition_tag_list.pop(-1)
                for sub_element in element.findall(tag):
                    if self._has_condition(sub_element, condition_tag_list, key_value):
                        condition_found = True
                        element = sub_element
                        break
                if not condition_found:
                    raise Exception('Could not find condition!')
            else:
                element = element.find(tag)
        return element

    def _get_from_tag_list(self, tag_list, key='value'):
        element = self._get_element_from_tag_list(tag_list)
        print(element)
        return element.get(key)

    def _set_from_tag_list(self, tag_list, key='value', value=None):
        if value is None:
            raise Exception(f'No value given to set for key "{key}"!')
        element = self._get_element_from_tag_list(tag_list)
        element.set(key, value)

    def _get_value_list(self, tag_list, values_from_tags):
        single_list = False
        if type(values_from_tags) == str:
            values_from_tags = [values_from_tags]
            single_list = True
        tag_list = tag_list[:]
        find_all_tag = tag_list.pop(-1)
        element = self.tree
        for tag in tag_list:
            element = element.find(tag)
        elements = element.findall(find_all_tag)
        return_list = []
        for element in elements:
            value_list = []
            for item in values_from_tags:
                sub_tag_list = [t.strip() for t in item.split(';')]
                sub_element = element
                for sub_tag in sub_tag_list:
                    sub_element = sub_element.find(sub_tag)
                value_list.append(sub_element.get('value'))
            if single_list:
                return_list.append(value_list[0])
            else:
                return_list.append(tuple(value_list))
        return return_list

    def list_all(self):
        for item in self.tree.iter():
            print(item)

    def save(self):
        self.tree.write(self.file_path)


class PSAfileWithPlot(PSAfile):

    def __init__(self, file_path):
        super().__init__(file_path)
        self.display_parameter_tags = []
        self.display_depth_tags = []
        self.display_nr_bins_tags = []
        self.display_nr_minor_bins_tags = []
        self.blueprint_display_parameter_tags = []

        self.parameter_min_tag = ''
        self.parameter_max_tag = ''

    def _get_tag_list_for_parameter(self, parameter):
        tag_list = []
        for tag in self.blueprint_display_parameter_tags:
            tag = tag.replace('<PARAMETER>', parameter)
            tag_list.append(tag)
        return tag_list

    @property
    def display_depth(self):
        return self._get_from_tag_list(self.display_depth_tags, key='value')

    @display_depth.setter
    def display_depth(self, max_depth):
        self._set_from_tag_list(self.display_depth_tags, key='value', value=str(max_depth))

    @property
    def nr_bins(self):
        return self._get_from_tag_list(self.display_nr_bins_tags, key='value')

    @nr_bins.setter
    def nr_bins(self, nr_bins):
        self._set_from_tag_list(self.display_nr_bins_tags, key='value', value=str(int(nr_bins)))
        
        bin_size = int(float(self.display_depth) / float(nr_bins))
        nr_minor_bins = '5'
        if bin_size == 5:
            nr_minor_bins = '1'
        elif bin_size == 10:
            nr_minor_bins = '2'
        self._set_from_tag_list(self.display_nr_minor_bins_tags, key='value', value=nr_minor_bins)

    def get_displayed_parameters(self):
        values_from_tags = 'Calc;FullName'
        return self._get_value_list(self.display_parameter_tags, values_from_tags)

    def get_parameter_range(self, parameter):
        if parameter not in self.get_displayed_parameters():
            raise Exception(f'Parameter "{parameter}" not found in display parameters')
        tag_list = self._get_tag_list_for_parameter(parameter)
        min_element = self._get_element_from_tag_list(tag_list + [self.parameter_min_tag])
        max_element = self._get_element_from_tag_list(tag_list + [self.parameter_max_tag])
        return min_element.get('value'), max_element.get('value')

    def set_parameter_range(self, parameter, min_value=None, max_value=None):
        if parameter not in self.get_displayed_parameters():
            raise Exception(f'Parameter "{parameter}" not found in display parameters')
        tag_list = self._get_tag_list_for_parameter(parameter)
        if min_value:
            min_element = self._get_element_from_tag_list(tag_list + [self.parameter_min_tag])
            min_element.set('value', str(min_value))
        if max_value:
            max_element = self._get_element_from_tag_list(tag_list + [self.parameter_max_tag])
            max_element.set('value', str(max_value))


class SeasavePSAfile(PSAfileWithPlot):
    def __init__(self, file_path):
        super().__init__(file_path)

        self.parameter_min_tag = 'MinimumValue'
        self.parameter_max_tag = 'MaximumValue'

        self.xmlcon_name_tags = ['Settings', 'ConfigurationFilePath']
        self.data_file_tags = ['Settings', 'DataFilePath']

        self.station_tags = ['Settings', 'HeaderForm', 'Prompt{{index==0}}']
        self.operator_tags = ['Settings', 'HeaderForm', 'Prompt{{index==1}}']
        self.ship_tags = ['Settings', 'HeaderForm', 'Prompt{{index==2}}']
        self.cruise_tags = ['Settings', 'HeaderForm', 'Prompt{{index==3}}']
        self.lat_tags = ['Settings', 'HeaderForm', 'Prompt{{index==4}}']
        self.lon_tags = ['Settings', 'HeaderForm', 'Prompt{{index==5}}']
        # self.pos_source_tags = ['Settings', 'HeaderForm', 'Prompt{{index==6}}']
        self.event_id_tags = ['Settings', 'HeaderForm', 'Prompt{{index==6}}']
        self.parent_event_id_tags = ['Settings', 'HeaderForm', 'Prompt{{index==7}}']
        self.add_samp_tags = ['Settings', 'HeaderForm', 'Prompt{{index==8}}']
        self.metadata_admin_tags = ['Settings', 'HeaderForm', 'Prompt{{index==9}}']
        self.metadata_conditions_tags = ['Settings', 'HeaderForm', 'Prompt{{index==10}}']

        self.display_depth_tags = ['Clients', 'DisplaySettings', 'Display', 'XYPlotData', 'Axes',
                    'Axis{{Calc;FullName;value==Scan Count}}', 'MaximumValue']

        self.display_nr_bins_tags = ['Clients', 'DisplaySettings', 'Display', 'XYPlotData', 'Axes',
                                     'Axis{{Calc;FullName;value==Scan Count}}', 'MajorDivisions']

        self.display_nr_minor_bins_tags = ['Clients', 'DisplaySettings', 'Display', 'XYPlotData', 'Axes',
                                     'Axis{{Calc;FullName;value==Scan Count}}', 'MinorDivisions']

        self.display_parameter_tags = ['Clients', 'DisplaySettings', 'Display', 'XYPlotData', 'Axes', 'Axis']

        self.blueprint_display_parameter_tags = ['Clients', 'DisplaySettings', 'Display', 'XYPlotData', 'Axes',
                                                 'Axis{{Calc;FullName;value==<PARAMETER>}}']

    @property
    def xmlcon_path(self):
        element = self._get_element_from_tag_list(self.xmlcon_name_tags)
        return element.get('value')

    @xmlcon_path.setter
    def xmlcon_path(self, file_path):
        file_path = file_path.strip('.xmlcon') + '.xmlcon'
        element = self._get_element_from_tag_list(self.xmlcon_name_tags)
        element.set('value', str(file_path))

    @property
    def data_path(self):
        element = self._get_element_from_tag_list(self.data_file_tags)
        return element.get('value')

    @data_path.setter
    def data_path(self, file_path):
        file_path = Path(file_path)
        stem = file_path.stem
        directory = file_path.parent
        data_file_path = Path(directory, f'{stem}.hex')
        element = self._get_element_from_tag_list(self.data_file_tags)
        element.set('value', str(data_file_path))

    @property
    def station(self):
        element = self._get_element_from_tag_list(self.station_tags)
        return element.get('value')

    @station.setter
    def station(self, station):
        element = self._get_element_from_tag_list(self.station_tags)
        value = f'Station: {station}'
        element.set('value', value)

    @property
    def operator(self):
        element = self._get_element_from_tag_list(self.operator_tags)
        return element.get('value')

    @operator.setter
    def operator(self, operator):
        element = self._get_element_from_tag_list(self.operator_tags)
        value = f'Operator: {operator}'
        element.set('value', value)

    @property
    def ship(self):
        element = self._get_element_from_tag_list(self.ship_tags)
        return element.get('value')

    @ship.setter
    def ship(self, ship):
        element = self._get_element_from_tag_list(self.ship_tags)
        value = f'Ship: {ship}'
        element.set('value', value)

    @property
    def cruise(self):
        element = self._get_element_from_tag_list(self.cruise_tags)
        return element.get('value')

    @cruise.setter
    def cruise(self, cruise):
        element = self._get_element_from_tag_list(self.cruise_tags)
        value = f'Cruise: {cruise}'
        element.set('value', value)

    @property
    def position(self):
        lat_element = self._get_element_from_tag_list(self.lat_tags)
        lon_element = self._get_element_from_tag_list(self.lon_tags)
        source_element = self._get_element_from_tag_list(self.pos_source_tags)
        return [lat_element.get('value'), lon_element.get('value'), source_element.get('value')]

    @position.setter
    def position(self, position):
        lat_element = self._get_element_from_tag_list(self.lat_tags)
        lon_element = self._get_element_from_tag_list(self.lon_tags)
        # source_element = self._get_element_from_tag_list(self.pos_source_tags)

        if len(position) == 2:
            position.append('Unknown')
        elif not position[2]:
            position.append('Unknown')

        lat_element.set('value', f'Latitud [GG MM.mm N]: {position[0]}')
        lon_element.set('value', f'Longitude [GG MM.mm E]: {position[1]}')
        # source_element.set('value', f'Position source: {position[2]}')

    @property
    def event_id(self):
        element = self._get_element_from_tag_list(self.event_id_tags)
        return element.get('value')

    @event_id.setter
    def event_id(self, id):
        element = self._get_element_from_tag_list(self.event_id_tags)
        value = f'EventID: {id}'
        element.set('value', value)

    @property
    def parent_event_id(self):
        element = self._get_element_from_tag_list(self.parent_event_id_tags)
        return element.get('value')

    @parent_event_id.setter
    def parent_event_id(self, id):
        element = self._get_element_from_tag_list(self.parent_event_id_tags)
        value = f'Parent EventID: {id}'
        element.set('value', value)

    @property
    def add_samp(self):
        element = self._get_element_from_tag_list(self.add_samp_tags)
        return element.get('value')

    @add_samp.setter
    def add_samp(self, add_samp):
        element = self._get_element_from_tag_list(self.add_samp_tags)
        value = f'Additional Sampling: {add_samp}'
        element.set('value', value)

    @property
    def metadata_admin(self):
        element = self._get_element_from_tag_list(self.metadata_admin_tags)
        string = element.get('value')
        return utils.metadata_string_to_dict(string.split(':', 1)[-1].strip())

    @metadata_admin.setter
    def metadata_admin(self, metadata_admin):
        string = utils.metadata_dict_to_string(metadata_admin)
        element = self._get_element_from_tag_list(self.metadata_admin_tags)
        value = f'Metadata admin: {string}'
        element.set('value', value)

    @property
    def metadata_conditions(self):
        element = self._get_element_from_tag_list(self.metadata_conditions_tags)
        string = element.get('value')
        return utils.metadata_string_to_dict(string)

    @metadata_conditions.setter
    def metadata_conditions(self, metadata_conditions):
        string = utils.metadata_dict_to_string(metadata_conditions)
        element = self._get_element_from_tag_list(self.metadata_conditions_tags)
        value = f'Metadata conditions: {string}'
        element.set('value', value)


class PlotPSAfile(PSAfileWithPlot):
    def __init__(self, file_path):
        super().__init__(file_path)

        self.parameter_min_tag = 'FixedMinimum'
        self.parameter_max_tag = 'FixedMaximum'

        self.title_tags = ['Title']

        self.display_parameter_tags = ['Axis']

        self.blueprint_display_parameter_tags = ['Axis{{Calc;FullName;value==<PARAMETER>}}']

        self.display_depth_tags = ['Axis{{Calc;FullName;value==Depth [fresh water, m]}}', 'FixedMaximum']

    @property
    def title(self):
        return self._get_element_from_tag_list(self.title_tags).get('value')

    @title.setter
    def title(self, title):
        self._get_element_from_tag_list(self.title_tags).set('value', title)


class DerivePSAfile(PSAfile):
    def __init__(self, file_path):
        super().__init__(file_path)

    def turn_tau_correction_on(self):
        self.set_tau_correction(True)

    def turn_tau_correction_off(self):
        self.set_tau_correction(False)

    def set_tau_correction(self, state):
        return
        state = str(int(state))
        for element in self.tree.find('CalcArray'):
            calc_element = element.find('Calc').find('ApplyTauCorrection')
            if calc_element is not None:
                calc_element.set('value', state)
        self.save()


class LoopeditPSAfile(PSAfile):
    def __init__(self, file_path):
        super().__init__(file_path)

    @property
    def depth(self):
        return self.tree.find('SurfaceSoakDepth').get('value')


if __name__ == '__main__':
    d = DerivePSAfile(r'C:\mw\git\ctd_config\SBE\processing_psa\Common/Derive.psa')
    d.turn_tau_correction_on()

    l = LoopeditPSAfile(r'C:\mw\git\ctd_config\SBE\processing_psa\Common/LoopEdit_deep.psa')

#     psa = SeasavePSAfile(r'C:\mw\git\ctd_config\SBE\seasave_psa\svea/Seasave.psa')
#     print('======')
#     print(psa.display_depth)
#     print('------')
#     print(psa.station)
#     print('------')
#     print(psa.operator)
#     print('------')
#     print(psa.ship)
#     print('------')
#     print(psa.cruise)

    # plot = PlotPSAfile(r'C:\mw\git\pre_system_svea\pre_system_svea\resources/File_2-SeaPlot_T_S_difference.psa')
    # psa.display_depth = 300
    # # psa.save()
    #
    # print(psa.display_depth)
    #
    # disp_par_list = psa.get_displayed_parameters()
    # print(disp_par_list)
    #
    # psa.set_parameter_range('Salinity, Practical [PSU]', max_value=22)
    # psa.save()

    psa = SeasavePSAfile(r'C:\mw\git\ctd_config\SBE\seasave_psa\svea/Seasave.psa')








