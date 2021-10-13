from .psa_file import PSAfile


class LoopeditPSAfile(PSAfile):
    def __init__(self, file_path):
        super().__init__(file_path)

    @property
    def depth(self):
        return self.tree.find('SurfaceSoakDepth').get('value')