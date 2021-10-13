


class CNVheader:
    def __init__(self, linebreak='\n'):
        self.linebreak = linebreak
        self.rows = []

    def add_row(self, row):
        self.rows.append(row.strip())

    def insert_row_after(self, row, after_str, ignore_if_string=None):
        for line in self.rows:
            if row == line:
                return
        for i, value in enumerate(self.rows[:]):
            if after_str in value:
                if ignore_if_string:
                    if ignore_if_string in self.rows[i+1]:
                        continue
                self.rows.insert(i+1, row.strip())
                break

    def append_to_row(self, string_in_row, append_string):
        for i, value in enumerate(self.rows[:]):
            if string_in_row in value:
                new_string = self.rows[i] + append_string.rstrip()
                if self.rows[i] == new_string:
                    continue
                self.rows[i] = new_string
                break

    def get_row_index_for_matching_string(self, match_string, as_list=False):
        index = []
        for i, value in enumerate(self.rows):
            if match_string in value:
                index.append(i)
        if not index:
            return None
        if as_list:
            return index
        if len(index) == 1:
            return index[0]
        return index

    def replace_string_at_index(self, index, from_string, to_string, ignore_if_present=True):
        if index is None:
            return
        if type(index) == int:
            index = [index]
        for i in index:
            if to_string in self.rows[i] and ignore_if_present:
                continue
            self.rows[i] = self.rows[i].replace(from_string, to_string)

    def replace_row(self, index, new_value):
        self.rows[index] = new_value.strip()