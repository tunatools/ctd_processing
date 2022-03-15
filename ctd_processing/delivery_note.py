import datetime
import pathlib

from ctd_processing import modify_cnv


class DeliveryNote:

    def __init__(self, directory=None, file_list=None, contact='', comment='', description=''):
        self._directory = None
        self._paths = None
        if directory:
            self._directory = pathlib.Path(directory)
            self._paths = [path for path in self._directory.iterdir() if path.suffix == '.cnv']
        elif file_list:
            self._paths = file_list
        else:
            raise Exception('No files selected for delivery note')
        self._contact = contact
        self._comment = comment
        self._description = description
        self._stem = None
        self._save_path = None
        self._data = None

        self._save_info()

    def __str__(self):
        return f'DeliveryNote'

    def _save_info(self):
        year_set = set()
        mprog_set = set()
        proj_set = set()
        orderer_set = set()
        for path in self._paths:
            header_form_info = modify_cnv.get_header_form_information(path)
            ctd_info = ctd_files.get_ctd_files_object(path)
            mprog_set.add(header_form_info.get('MPROG', ''))
            proj_set.add(header_form_info.get('PROJ', ''))
            year_set.add(str(ctd_info.year))
            orderer_set.add(header_form_info.get('ORDERER', ''))

        mprog_set.discard('')
        proj_set.discard('')
        orderer_set.discard('')

        all_orderers = []
        for ord in orderer_set:
            all_orderers.extend([item.strip() for item in ord.split(',')])

        self._data = {}
        self._data['MYEAR'] = ', '.join(sorted(year_set))
        self._data['DTYPE'] = 'PROFILE'
        self._data['MPROG'] = ', '.join(sorted(mprog_set))
        self._data['ORDERER'] = ', '.join(sorted(set(all_orderers)))
        self._data['PROJ'] = ', '.join(sorted(proj_set))
        self._data['RLABO'] = 'SMHI'
        self._data['REPBY'] = self._contact
        self._data['COMNT_DN'] = self._comment
        self._data['DESCR'] = self._description
        self._data['FORMAT'] = 'PROFILE'
        self._data['VERSION'] = datetime.datetime.now().strftime('%Y-%m-%d')


        # self._data['data kontrollerad av'] = 'Leverantör'
        # self._data['format'] = 'PROFILE'
        # self._data['projekt'] = ', '.join(sorted(proj_set))
        # self._data['rapporterande institut'] = 'SMHI'
        # self._data['datatype'] = 'PROFILE'
        # self._data['beskrivning av dataset'] = self._description
        # self._data['övervakningsprogram'] = ', '.join(sorted(mprog_set))
        # self._data['beställare'] = ', '.join(sorted(set(all_orderers)))
        # self._data['provtagningsår'] = ', '.join(sorted(year_set))
        # self._data['kontaktperson'] = self._contact
        # self._data['kommentar'] = self._comment

    def write_to_file(self, directory):
        path = pathlib.Path(directory, 'delivery_note.txt')
        lines = []
        for key, value in self._data.items():
            lines.append(f'{key}: {value}')
        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))
        return path


if __name__ == '__main__':
    dn = DeliveryNote(r'C:\mw\temp_ctd_pre_system_data_root\cnv')
    dn.write_to_file(r'C:\mw\temp_ctd_pre_system_export')


