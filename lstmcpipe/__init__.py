import os
from pathlib import Path

lstmcpipe_root_dir = Path(__file__).absolute().parents[1]
prod_logs = os.getenv('LSTMCPIPE_PROD_LOGS') if os.getenv('LSTMCPIPE_PROD_LOGS') is not None \
    else os.path.join(os.getenv('HOME'), 'LSTMCPIPE_PROD_LOGS')

__version__ = "0.6.1"
