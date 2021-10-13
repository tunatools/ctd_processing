from .psa_file import PSAfile


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