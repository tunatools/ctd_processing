

class DVdataDelivery:

    def create_sensorinfo_summary_file(self):
        self._sensorinfo_file = sensor_info.create_sensor_info_summary_file_from_directory(self._output_dir)

    def create_metadata_summary_file(self):
        self._sensorinfo_file = sensor_info.create_sensor_info_summary_file_from_directory(self._output_dir)






