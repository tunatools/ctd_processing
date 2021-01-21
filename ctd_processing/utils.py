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