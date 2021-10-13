from .psa_file_with_plot import PSAfileWithPlot


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