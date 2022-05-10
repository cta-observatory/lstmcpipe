from pathlib import Path
from lstmcpipe import prod_logs


def test_create_log_files():
    from ..lstmcpipe_tree_path import create_log_files

    logs, scancel_file, log_dir = create_log_files('dummy_prodID')

    assert "log_file" in logs.keys()
    assert "debug_file" in logs.keys()

    assert isinstance(logs["log_file"], Path)
    assert isinstance(logs["debug_file"], Path)
    assert isinstance(scancel_file, Path)

    assert scancel_file.exists()

    scancel_file.unlink()
    log_dir.rmdir()


def test_update_scancel_file():
    from ..lstmcpipe_tree_path import create_log_files, update_scancel_file

    _, scancel_file, log_dir = create_log_files("dummy_prodID")

    update_scancel_file(scancel_file, "1234")
    with open(scancel_file) as f:
        lines = f.readlines()
    assert lines == ["scancel 1234"]

    update_scancel_file(scancel_file, "5678")
    with open(scancel_file) as f:
        lines = f.readlines()
    assert lines == ["scancel 1234,5678"]

    scancel_file.unlink()
    log_dir.rmdir()


def test_backup_log():
    from ..lstmcpipe_tree_path import backup_log

    dummy_file = Path('./test_file.txt')
    dummy_file.touch()

    saved_file_0 = Path('./BACKUP_00_test_file.txt')
    saved_file_1 = Path('./BACKUP_01_test_file.txt')

    backup_log(dummy_file)
    assert saved_file_0.exists()
    backup_log(dummy_file)
    assert saved_file_1.exists()

    dummy_file.unlink()
    saved_file_0.unlink()
    saved_file_1.unlink()


def test_create_log_dir():
    from ..lstmcpipe_tree_path import create_log_dir

    log_dirname = create_log_dir("test_prodID")
    assert log_dirname.is_dir()
    assert log_dirname.name == prod_logs.joinpath("logs_test_prodID").name
    log_dirname.rmdir()
