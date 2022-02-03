from ctd_processing import cnv
from ctd_processing import xmlcon


class ParamReported:
    def __init__(self, cnv_file_path=None, instrument_file=None):
        self.cnv_file_path = cnv_file_path
        self.instrument_file = instrument_file

        # self.cnv_xml_info = xmlcon.CNVfileXML(self.cnv_file_path).get_sensor_info()
        self.cnv_reported_names = cnv.get_reported_names_in_cnv(self.cnv_file_path)

    def get_reported_name(self, parameter, sensor_id=None):
        # 1: Hitta instrumentinformation baserat på parameter och sensor_id
        instrument_info = self.instrument_file.get_info_for_parameter_and_sensor_id(parameter=parameter,
                                                                                    sensor_id=sensor_id)

        # print('get_reported_name', parameter, sensor_id)
        # for par in self.cnv_reported_names:
        #     print('-', par)

        # 2: Matcha CNV_CODE i instrumentinformationen mot rapporterade name i cnv-filen
        #   a: Matcha CNV_CODE
        #   b: kontrollera om sensor 1 eller 2
        for name in self.cnv_reported_names:
            # print('NAME', ':', instrument_info['CNV_NAME'], ':', name, ':', parameter)
            # print('parameter', parameter, name)
            if name.startswith(parameter):
                print('OK parameter', parameter, name)
                return name

            if instrument_info['CNV_NAME'] not in name:
            # if parameter not in name:
                continue
            print('name0', ':', instrument_info['CNV_NAME'], ':', name, ':', parameter)
            for cnv_code in instrument_info['cnv_codes']:
                if not self._reported_name_matches_cnv_code(name, cnv_code):
                    continue
                # print('OK')
                if self._parameter_is_sensor_1(parameter) and self._reported_name_is_sensor_1(name):
                    print('name1', cnv_code, name, parameter)
                    return name
                if self._parameter_is_sensor_2(parameter) and self._reported_name_is_sensor_2(name):
                    print('name2', cnv_code, name, parameter)
                    return name
        raise Exception(f'No reported name found in for parameter "{parameter}" in cnv file: {self.cnv_file_path}')

    @staticmethod
    def _parameter_is_sensor_1(parameter):
        if parameter.replace(' ', '')[-2] == ',':
            return False
        return True

    @staticmethod
    def _parameter_is_sensor_2(parameter):
        if parameter.endswith('2'):
            return True
        return False

    @staticmethod
    def _reported_name_matches_cnv_code(rep_name, cnv_code):
        if rep_name.startswith(cnv_code):
            return True
        return False

    @staticmethod
    def _reported_name_is_sensor_1(rep_name):
        if '[' not in rep_name:
            return False
        name = rep_name.split('[')[-2]
        compact_name = name.replace(' ', '')
        if compact_name[-2] == ',':
            return False
        return True

    @staticmethod
    def _reported_name_is_sensor_2(rep_name):
        if '[' not in rep_name:
            return False
        name = rep_name.split('[')[-2]
        compact_name = name.replace(' ', '')
        if compact_name.endswith(',2'):
            return True
        return False


