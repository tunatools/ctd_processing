

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
                form = f'{self.get_format()} (from info file)'
            else:
                form = f'{self.get_format()} (calculated from data)'
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

    def get_format(self, value=None):
        if self.use_cnv_info_format:
            return self.cnv_info_object.format
        if self._nr_decimals is None:
            form = f'{self._tot_value_length}{self._value_format}'
        else:
            if value and self._value_format == 'e' and str(value).startswith('-'):
                form = f'{self._tot_value_length}.{self._nr_decimals-1}{self._value_format}'
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
        return '{:{}}'.format(self.data[index], self.get_format(self.data[index]))

    def set_active(self, is_active):
        self.active = is_active