
class Ship:
    name = ''
    short_name = ''
    ship_id = ''

    def __init__(self, fstem=None, **kwargs):
        self.fstem = fstem.upper()

    def __repr__(self):
        return f'Ship: {self.name}({self.short_name})'


class FinnishShip(Ship):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def serial_number(self):
        if not self.fstem:
            raise AssertionError('Attribute fstem not set')
        # sv19d0003.hex
        # self.serial_number = fstem[3:7]
        if len(self.fstem) == 12:
            snum = self.fstem[5:8]
        else:  # if series is 4 digits
            snum = self.fstem[5:8]
        # justerar till 4 siffror
        return snum.zfill(4)


class SBE09(Ship):
    name = 'SBE09'
    short_name = 'SBE09'
    ship_id = ''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_info()

    def _load_info(self):
        name, inst_nr, date_str, time_str, ctry_code, ship_code, serno = self.fstem.split('_')
        self.ship_id = '_'.join([ctry_code, ship_code])

    @property
    def serial_number(self):
        if not self.fstem:
            raise AssertionError('Attribute fstem not set')
        return self.fstem.split('_')[-1][:4]


class Dana(Ship):
    name = 'Dana'
    short_name = '26DA'
    ship_id = '26_01'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def serial_number(self):
        if not self.fstem:
            raise AssertionError('Attribute fstem not set')
        # Dana filenames usually look lite this:  26DA.2016.10.1.hdr
        # Merge Cruisenr and activity number 1001. Add zeros.
        # If self.serial_number is over 100 add this to next cruise nr 1000
        if int(self.fstem.split('.')[3].zfill(2)) > 99:
            return str(int(self.fstem.split('.')[2]) + 1).zfill(2) + self.fstem.split('.')[3][1:]
        else:
            return self.fstem.split('.')[2].zfill(2) + self.fstem.split('.')[3].zfill(2)


class Aranda(FinnishShip):
    name = 'Aranda'
    short_name = 'AR'
    ship_id = '34_01'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Aura(FinnishShip):
    name = 'Aura'
    short_name = 'AU'
    ship_id = '34_07'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Meri(FinnishShip):
    name = 'Meri'
    short_name = 'ME'
    ship_id = '34_02'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Svea(Ship):
    name = 'Svea'
    short_name = 'SV'
    ship_id = '77_10'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def serial_number(self):
        if not self.fstem:
            raise AssertionError('Attribute fstem not set')
        return self.fstem[5:9]


def get_ship_object_from_sbe09(fstem):
    name, inst_nr, date_str, time_str, ctry_code, ship_code, serno = fstem.split('_')
    ship_id = '_'.join([ctry_code, ship_code])
    for obj in [Dana, Aranda, Meri, Aura, Svea]:
        if obj.ship_id == ship_id:
            return obj(fstem=fstem)


SHIPS = {}
for Ship in [SBE09, Dana, Aranda, Meri, Aura, Svea]:
    SHIPS[Ship.short_name] = Ship

