from pathlib import Path
import xml
import xml.etree.ElementTree as ET
import datetime


class XMLCONfile:
    def __init__(self, file_path, tree: xml.etree.ElementTree = False):
        self.file_path = Path(file_path)
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


class CNVfileXML:

    def __init__(self, file_path):
        self.path = Path(file_path)
        lines = ['<?xml version="1.0" encoding="UTF-8"?>\n']
        is_xml = False
        with open(file_path) as fid:
            for line in fid:
                if line.startswith('# <Sensors count'):
                    is_xml = True
                if is_xml:
                    lines.append(line[2:])
                if line.startswith('# </Sensors>'):
                    break
        xmlstring = ''.join(lines)
        self.tree = ET.ElementTree(ET.fromstring(xmlstring))

    def get_sensor_info(self):
        index = {}
        sensor_list = []
        for i, sensor in enumerate(self.tree.findall('sensor')):
            child_list = sensor.getchildren()
            if not child_list:
                continue
            child = child_list[0]
            par = child.tag
            nr = child.find('SerialNumber').text
            calibration_date = child.find('CalibrationDate').text
            if nr is None:
                nr = ''
            index.setdefault(par, [])
            index[par].append(i)
            data = {'channel': int(sensor.attrib['Channel']),
                    'parameter': par,
                    'serial_number': nr,
                    'calibration_date': datetime.datetime.strptime(calibration_date, '%d-%b-%y')}
            sensor_list.append(data)
        for par, index_list in index.items():
            if len(index_list) == 1:
                continue
            for nr, i in enumerate(index_list):
                sensor_list[i]['parameter'] = f'{sensor_list[i]["parameter"]}_{nr+1}'
        return sensor_list


if __name__ == '__main__':
    file_path = Path(r'C:\mw\temp_svea\_input_files/SBE09_1387_20200207_0801_77_10_0120.XMLCON')
    cnv_path = Path(r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210413_1113_77SE_00_0278.cnv')

    # xml = XMLCONfile(file_path)
    # xml.print_sensors()

    xml = CNVfileXML(cnv_path)
    sensor_list = xml.get_sensor_info()