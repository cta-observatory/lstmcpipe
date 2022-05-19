"""Helpers to setup logging. Copied and adapted from
https://github.com/fact-project/aict-tools/blob/ee091fc933110ff008e32df02ee12a97e412e8b3/aict_tools/logging.py
"""

import logging


def setup_logging(logfile=None, verbose=False):
    """
    Setup logging using the logging module
    from the python standard library. A handler for
    the terminal and optionally a file handler get setup,
    the logger is using INFO or DEBUG depending on the
    value of `verbose`.
    Numba logs are filtered if they are not WARNING or above,
    because numba creates thousands of lines in the output.

    Parameters:
    -----------
    logfile: str or path-like
        File to save logs to.
    verbose: boolean
        Whether to enable debug logging

    Returns:
    --------
    logging.Logger
    """

    level = logging.INFO
    if verbose is True:
        level = logging.DEBUG

    log = logging.getLogger()
    log.level = level

    stream_formatter = logging.Formatter(fmt="%(levelname)-8s|%(message)s", datefmt="%H:%M:%S")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    log.addHandler(stream_handler)

    if logfile is not None:
        file_formatter = logging.Formatter(
            fmt="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(file_formatter)
        log.addHandler(file_handler)
        log.debug("Added logging handler with log file {}".format(logfile))

    # numba produces a ton of logs when set to debug and the solution of using enviroment variables seems to be
    # inconsistent. We dont expect to look through thousands of lines of numba logging anytime soon, so it gets
    # ignored explicitly
    logging.getLogger("numba").setLevel(logging.WARNING)

    return log
