import re
import lstmcpipe


def test_version():
    with open("lstmcpipe/__init__.py") as f:
        __version__ = re.search('^__version__ = "(.*)"$', f.read()).group(1)
    assert lstmcpipe.__version__ == __version__
