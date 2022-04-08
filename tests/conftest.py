import sys

collect_ignore = []

if sys.version_info[0] < 3:
    collect_ignore_glob = ["*_py3.py"]
else:
    collect_ignore_glob = ["*_py2.py"]
