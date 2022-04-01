import re

import lstmcpipe


def test_version():
    with open("lstmcpipe/__init__.py") as f:
        version = re.search('"(.*?)"', f.readlines()[-1]).group(1)
    assert lstmcpipe.__version__ == version
