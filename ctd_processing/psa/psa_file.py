import xml.etree.ElementTree as ET
import pathlib


class PSAfile:
    """
    psa-files are configuration files used for seabird processing.
    """
    def __init__(self, file_path):
        self.file_path = pathlib.Path(file_path)
        self.tree = ET.parse(self.file_path)

    def _has_condition(self, element, tag_list, condition):
        for tag in tag_list:
            element = element.find(tag)
        key, value = [item.strip() for item in condition.split('==')]
        # Add vildcard here
        v = element.get(key)
        if element.get(key) == value:
            return True

    def _get_element_from_tag_list(self, tag_list):
        element = self.tree
        for tag in tag_list:
            if '{{' in tag:
                condition_found = False
                tag, condition = tag.split('{{')
                condition = condition.strip('}}')
                condition_tag_list = [item.strip() for item in condition.split(';')]
                key_value = condition_tag_list.pop(-1)
                for sub_element in element.findall(tag):
                    if self._has_condition(sub_element, condition_tag_list, key_value):
                        condition_found = True
                        element = sub_element
                        break
                if not condition_found:
                    raise Exception('Could not find condition!')
            else:
                element = element.find(tag)
        return element

    def _get_from_tag_list(self, tag_list, key='value'):
        element = self._get_element_from_tag_list(tag_list)
        print(element)
        return element.get(key)

    def _set_from_tag_list(self, tag_list, key='value', value=None):
        if value is None:
            raise Exception(f'No value given to set for key "{key}"!')
        element = self._get_element_from_tag_list(tag_list)
        element.set(key, value)

    def _get_value_list(self, tag_list, values_from_tags):
        single_list = False
        if type(values_from_tags) == str:
            values_from_tags = [values_from_tags]
            single_list = True
        tag_list = tag_list[:]
        find_all_tag = tag_list.pop(-1)
        element = self.tree
        for tag in tag_list:
            element = element.find(tag)
        elements = element.findall(find_all_tag)
        return_list = []
        for element in elements:
            value_list = []
            for item in values_from_tags:
                sub_tag_list = [t.strip() for t in item.split(';')]
                sub_element = element
                for sub_tag in sub_tag_list:
                    sub_element = sub_element.find(sub_tag)
                value_list.append(sub_element.get('value'))
            if single_list:
                return_list.append(value_list[0])
            else:
                return_list.append(tuple(value_list))
        return return_list

    def list_all(self):
        for item in self.tree.iter():
            print(item)

    def save(self):
        self.tree.write(self.file_path)