

if __name__ == '__main__':
    from ctd_processing.xmlcon import cnv_file
    file_path = r'C:\mw\temp_ctd_pre_system_data_root\cnv/SBE09_1387_20210413_1113_77SE_00_0278.cnv'
    par_list = cnv_file.get_parameter_list(file_path)
    for par in par_list:
        print(par)

    sensor_info = cnv_file.get_sensor_info(file_path)