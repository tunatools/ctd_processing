import pathlib
import xml
import xml.etree.ElementTree as ET


class XMLCONfile:
    def __init__(self, file_path, tree: xml.etree.ElementTree = False):
        self.file_path = pathlib.Path(file_path)
        if tree:
            self.tree = tree
        else:
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
