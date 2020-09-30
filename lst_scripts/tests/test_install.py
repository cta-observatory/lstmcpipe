import lst_scripts


def test_version():
    with open("lst_scripts/version.py") as f:
        __version__ = re.search('^__version__ = "(.*)"$', f.read()).group(1)
    assert lst_scripts.__version__ == __version__
