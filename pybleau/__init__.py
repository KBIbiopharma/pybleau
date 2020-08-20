from os.path import dirname, isfile, join
from subprocess import check_output
from collections import namedtuple


__version__ = "0.5.4"


try:
    _build_file = join(dirname(__file__), "build.txt")
    if isfile(_build_file):
        with open(_build_file) as f:
            __build__ = f.read().strip()
    else:
        # If no build file, we are on a dev machine: try to display the git
        # hash instead:
        git_hash = check_output("git rev-parse --short HEAD", shell=True)
        __build__ = git_hash.strip()
except Exception:
    __build__ = "XX"


# API version of the version:
_VersionInfo = namedtuple("_VersionInfo", ["version", "build"])


def _repr_version_info(self):
    """ __repr__ for a _VersionInfo object. """
    return "version: {}, build: {}".format(self.version, self.build)


_VersionInfo.__repr__ = _repr_version_info

version_info = _VersionInfo(__version__, __build__)
