from ctd_processing.sensor_info.sensor_info_file import SensorInfoFiles
from ctd_processing import sensor_info


if __name__ == '__main__':
    if 1:
        directory = r'C:\mw\temp_ctd_pre_system_data_root\cnv'
        s = SensorInfoFiles(directory)
        s.write_summary_to_file()

    if 0:
        from ctd_processing import xmlcon
        from ctd_processing import cnv
        instrument_file_path = r'C:\mw\git\ctd_config/Instruments.xlsx'
        # file_path = r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210921_0656_77SE_00_0814.cnv'
        # file_path = r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210417_2359_77SE_00_0300.cnv'
        file_path = r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210413_1113_77SE_00_0278.cnv'
        sensor_info_obj = sensor_info.get_sensor_info_object(instrument_file_path)
        sensor_info_obj.create_file_from_cnv_file(file_path)

        xml_info = xmlcon.CNVfileXML(file_path).get_sensor_info()
        name_info = cnv.get_parameter_channels_and_names_from_cnv(file_path)
    if 0:
        from ctd_processing.sensor_info import param_reported
        from ctd_processing.sensor_info import instrument_file

        file_path = r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210413_1113_77SE_00_0278.cnv'
        instrument_file_path = r'C:\mw\git\ctd_config/Instruments.xlsx'
        instrument = instrument_file.InstrumentFile(instrument_file_path)
        pr = param_reported.ParamReported(file_path, instrument)

        print(pr.get_reported_name('Temperature', '6378'))
        print(pr.get_reported_name('Temperature, 2', '6384'))
