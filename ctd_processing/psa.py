from pathlib import Path

import xml.etree.ElementTree as ET


class PSAfile:
    """
    psa-files are configuration files used for seabird processing.
    """
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.tree = ET.parse(self.file_path)

    def list_all(self):
        for item in self.tree.iter():
            print(item)


class SeasavePSAfile(PSAfile):
    def __init__(self, file_path):
        super().__init__(file_path)

    @property
    def xmlcon_name(self):
        return self.tree.find('Settings').find('ConfigurationFilePath').get('value')

    @xmlcon_name.setter
    def xmlcon_name(self, file_name):
        file_name = file_name.strip('.xmlcon') + '.xmlcon'
        self.tree.find('Settings').find('ConfigurationFilePath').set('value', file_name)


if __name__ == '__main__':
    psa = SeasavePSAfile(r'C:\mw\temp_svea\temp_psa/Seasave.psa')
    print(psa.xmlcon_name)


