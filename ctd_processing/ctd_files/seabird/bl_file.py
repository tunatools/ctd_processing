

class BlFile:
    def __init__(self, file_path, **kwargs):
        if file_path.suffix != '.bl':
            raise Exception(f'Given file is not a .bl file: {file_path}')
        self.file_path = file_path

        self._number_of_bottles = None

        self._save_number_of_bottles()

    @property
    def number_of_bottles(self):
        return self._number_of_bottles

    def _save_number_of_bottles(self):
        self._number_of_bottles = 0
        with open(self.file_path) as fid:
            for nr, line in enumerate(fid):
                stripped_line = line.strip()
                if nr > 1 and stripped_line:
                    self._number_of_bottles += 1