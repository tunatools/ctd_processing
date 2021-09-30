from pathlib import Path


def git_version():
    """
    Return current version of this github-repository
    :return: str
    """
    version_file = Path(Path(__file__).absolute().parent.parent, '.git', 'FETCH_HEAD')
    if version_file.exists():
        f = open(version_file, 'r')
        version_line = f.readline().split()
        version = version_line[0][:7]  # Is much longer but only the first 7 letters are presented on Github
        repo = version_line[-1]
        return 'github version "{}" of repository {}'.format(version, repo)
    else:
        return ''


def metadata_string_to_dict(string):
    key_value = [item.strip() for item in string.split('#')]
    data = {}
    for key_val in key_value:
        key, value = [item.strip() for item in key_val.split(':')]
        data[key] = value
    return data


def metadata_dict_to_string(data):
    string_list = []
    for key, value in data.items():
        string_list.append(f'{key}: {value}')
    string = ' # '.join(string_list)
    return string