import pytest

from lstmcpipe.io.data_management import check_data_path, get_input_filelist


@pytest.fixture()
def create_tmp_dir(tmp_path):
    test_dir = tmp_path / 'data'
    test_dir.mkdir()
    return test_dir


@pytest.fixture()
def create_tmp_subdir(tmp_path):
    test_dir = tmp_path / 'data' / 'subdir'
    test_dir.mkdir()
    return test_dir


@pytest.mark.xfail(raises=ValueError)
def test_check_data_path_raise_value_error(create_tmp_dir):
    check_data_path(create_tmp_dir)


def test_get_input_filelist(create_tmp_dir, create_tmp_subdir):
    for i in range(2):
        with open(create_tmp_dir.joinpath(f'LST-1.1.Run00101.{i:05d}.simtel.fz'), 'w'):
            pass
        with open(create_tmp_dir.joinpath(f'LST-1.1.Run00102.{i:05d}.h5'), 'w'):
            pass
    with open(create_tmp_dir.joinpath('some_file.log'), 'w'):
        pass
    for i in range(2):
        with open(create_tmp_subdir.joinpath(f'LST-1.1.Run00103.{i:05d}.simtel.fz'), 'w'):
            pass

    assert len(get_input_filelist(create_tmp_dir)) == 6  # 5 files plus subdir
    assert len(get_input_filelist(create_tmp_dir, glob_pattern="*.h5")) == 2
    assert len(get_input_filelist(create_tmp_dir, glob_pattern="**/*.simtel.fz")) == 4
