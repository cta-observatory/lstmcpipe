"""Helpers to setup logging. Copied and adapted from 
https://github.com/fact-project/aict-tools/blob/ee091fc933110ff008e32df02ee12a97e412e8b3/aict_tools/logging.py
"""

import logging


def setup_logging(logfile=None, verbose=False):

    level = logging.INFO
    if verbose is True:
        level = logging.DEBUG

    log = logging.getLogger()
    log.level = level

    stream_formatter = logging.Formatter(
            fmt="%(levelname)s\n%(message)s\n",
            datefmt="%H:%M:%S",
            )
    stream_handler  = logging.StreamHandler()
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

    return log
