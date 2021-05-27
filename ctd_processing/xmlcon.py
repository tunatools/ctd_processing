from pathlib import Path

import xml.etree.ElementTree as ET


class XMLCONfile:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tree = ET.parse(file_path)

    def get_sensor_info(self):
        index = {}
        sensor_list = []
        for i, sensor in enumerate(self.tree.find('Instrument').find('SensorArray').findall('Sensor')):
            child = sensor.getchildren()[0]
            par = child.tag
            nr = child.find('SerialNumber').text
            if nr is None:
                nr = ''
            index.setdefault(par, [])
            index[par].append(i)
            data = {'parameter': par,
                    'serial_number': nr}
            sensor_list.append(data)
        for par, index_list in index.items():
            if len(index_list) == 1:
                continue
            for nr, i in enumerate(index_list):
                sensor_list[i]['parameter'] = f'{sensor_list[i]["parameter"]}_{nr+1}'
        return sensor_list

    def print_sensors(self):
        for sensor in self.get_sensor_info():
            print(sensor.get('serial_number', ''), ': ',  sensor.get('parameter', ''))

    @property
    def serial_number(self):
        for sensor in self.tree.find('Instrument').find('SensorArray').findall('Sensor'):
            child = sensor.getchildren()[0]
            if child.tag == 'PressureSensor':
                return child.find('SerialNumber').text
        return None


if __name__ == '__main__':
    file_path = Path(r'C:\mw\temp_svea\_input_files/SBE09_1387_20200207_0801_77_10_0120.XMLCON')

    xml = XMLCONfile(file_path)
    xml.print_sensors()