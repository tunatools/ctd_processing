import pathlib
import subprocess
import threading
import psutil


def git_version():
    """
    Return current version of this github-repository
    :return: str
    """
    version_file = pathlib.Path(pathlib.Path(__file__).absolute().parent.parent, '.git', 'FETCH_HEAD')
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


def _get_running_programs():
    program_list = []
    for p in psutil.process_iter():
        program_list.append(p.name())
    return program_list


def _run_subprocess(line):
    subprocess.run(line)

def run_program(program, line):
    if program in _get_running_programs():
        raise ChildProcessError(f'{program} is already running!')
    t = threading.Thread(target=_run_subprocess(line))
    t.daemon = True  # close pipe if GUI process exits
    t.start()
