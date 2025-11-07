import ctadata
import fnmatch
import os
import logging
from functools import wraps
from pathlib import Path
from ctadata.api import APIClient

# SCRATCH is defined in environment variables at CSCS. https://docs.cscs.ch/platforms/mlp/#file-systems-and-storage
# SCRATCH=/iopsstor/scratch/cscs/$USER

log = logging.getLogger(__name__)

api = APIClient(dev_instance=False)
api.token_update_interval = 360000
api.init_agent()

# Cache configuration
CACHE_ROOT = Path(os.environ.get("SCRATCH", "/tmp")) / "lstmcpipe_cache"
CACHE_ROOT.mkdir(parents=True, exist_ok=True)


def _remote_to_cache_path(remote_path):
    """
    Convert a remote dCache path to a local cache path.
    
    Removes leading slashes and preserves the directory structure.
    
    Parameters
    ----------
    remote_path : str
        Remote path on dCache
        
    Returns
    -------
    cache_path : Path
        Local cache path in SCRATCH
        
    Examples
    --------
    >>> _remote_to_cache_path("/dCache/prod5/simtel/run_001.h5")
    Path("$SCRATCH/lstmcpipe_cache/dCache/prod5/simtel/run_001.h5")
    """
    # Remove leading slashes to make path relative
    relative_path = remote_path.lstrip("/")
    return CACHE_ROOT / relative_path


def _is_cached_file_valid(cache_path):
    """
    Check if a cached file exists and is valid (not empty).
    
    Parameters
    ----------
    cache_path : Path
        Path to the cached file
        
    Returns
    -------
    bool
        True if file exists and is not empty
    """
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return False
    
    # Check if file is not empty
    if cache_path.is_file() and cache_path.stat().st_size == 0:
        log.warning(f"Cached file {cache_path} is empty, will re-download")
        return False
    
    return True


def _ensure_cache_dir(cache_path):
    """
    Ensure the parent directory of a cache path exists.
    
    Parameters
    ----------
    cache_path : Path
        Path to the cache file/directory
    """
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)


def ensure_agent_running(func):
    """
    Decorator to ensure the ctadata agent is running before executing a function.
    Automatically starts the agent if needed.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # start_agent()
        pass
        return func(*args, **kwargs)
    return wrapper


def start_agent():
    """
    Start the CTA data agent if not already running
    """
    api = APIClient(dev_instance=False)
    api.init_agent()


@ensure_agent_running
def list_files_in_dir(directory, pattern="*"):
    """
    List all files in a directory matching a pattern and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory
    pattern: str
        glob pattern to match files

    Returns
    -------
    matched_files: list
        list of files in the directory matching the pattern
    """
    all_files =  ctadata.list_dir(directory)
    matched_files = [f for f in all_files if fnmatch.fnmatch(f, pattern)]
    return [directory + f for f in matched_files]


@ensure_agent_running
def list_simtel_files_in_dir(directory):
    """
    List all simtel files in a directory and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory

    Returns
    -------
    simtel_files: list
        list of simtel files in the directory
    """
    return list_files_in_dir(directory, pattern="*.simtel.gz")


@ensure_agent_running
def list_h5_files_in_dir(directory):
    """
    List all h5 files in a directory and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory

    Returns
    -------
    h5_files: list
        list of h5 files in the directory
    """
    return list_files_in_dir(directory, pattern="*.h5")


@ensure_agent_running
def list_dl1_files_in_dir(directory):
    """
    List all dl1 files in a directory and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory

    Returns
    -------
    dl1_files: list
        list of dl1 files in the directory
    """
    return list_files_in_dir(directory, pattern="dl1*.h5")


@ensure_agent_running
def list_dl2_files_in_dir(directory):
    """
    List all dl2 files in a directory and returns their full paths

    Parameters
    ----------
    directory: str
        path to a directory

    Returns
    -------
    dl2_files: list
        list of dl2 files in the directory
    """
    return list_files_in_dir(directory, pattern="dl2*.h5")


@ensure_agent_running
def get_file(remote_path, local_path):
    """
    Download a file from dCache to local path with automatic caching.
    
    First checks if the file exists in the SCRATCH cache. If found and valid,
    uses the cached version. Otherwise, downloads from dCache and caches it.

    Parameters
    ----------
    remote_path: str
        path to the file on dCache
    local_path: str
        path to save the file locally
    use_cache: bool, optional
        If True (default), check cache before downloading
    force_download: bool, optional
        If True, bypass cache and force re-download (default: False)
        
    Returns
    -------
    str
        Path to the downloaded file (either from cache or freshly downloaded)
    """
    local_path = Path(local_path)
    cache_path = _remote_to_cache_path(remote_path)
    
    # Check if file is already in cache
    if _is_cached_file_valid(cache_path):
        log.info(f"Cache HIT: Using cached file from {cache_path}")
        # Copy from cache to requested local path if different
        if cache_path != local_path:
            _ensure_cache_dir(local_path)
            import shutil
            shutil.copy2(cache_path, local_path)
        return str(local_path)
    
    # Cache MISS - download to cache first
    log.info(f"Cache MISS: Downloading {remote_path} to cache")
    _ensure_cache_dir(cache_path)
    
    try:
        ctadata.fetch_and_save_file(remote_path, save_to_fn=str(cache_path))
        
        # Validate downloaded file
        if not _is_cached_file_valid(cache_path):
            raise RuntimeError(f"Downloaded file {cache_path} is invalid (empty or missing)")
        
        # Copy from cache to requested local path if different
        if cache_path != local_path:
            _ensure_cache_dir(local_path)
            import shutil
            shutil.copy2(cache_path, local_path)
        
        log.info(f"Successfully cached and saved to {local_path}")
        return str(local_path)
    
    except Exception as e:
        log.error(f"Failed to download {remote_path}: {e}")
        # Clean up failed cache file if it exists
        if cache_path.exists():
            cache_path.unlink()
        raise


@ensure_agent_running
def get_dir(remote_dir, local_dir):
    """
    Download all files from a remote directory to a local directory with caching.
    
    First checks if files exist in the SCRATCH cache. Downloads only missing files.

    Parameters
    ----------
    remote_dir: str
        path to the remote directory on dCache
    local_dir: str
        path to the local directory
    force_download: bool, optional
        If True, bypass cache and force re-download (default: False)
        
    Returns
    -------
    str
        Path to the local directory
    """
    local_dir = Path(local_dir)
    cache_dir = _remote_to_cache_path(remote_dir)
    
    # Check if directory is already cached
    if cache_dir.exists() and cache_dir.is_dir():
        cached_files = list(cache_dir.rglob("*"))
        if cached_files:
            log.info(f"Cache HIT: Using cached directory from {cache_dir}")
            # Copy from cache to requested local directory
            if cache_dir != local_dir:
                import shutil
                _ensure_cache_dir(local_dir)
                if local_dir.exists():
                    shutil.rmtree(local_dir)
                shutil.copytree(cache_dir, local_dir)
            return str(local_dir)
    
    # Cache MISS - download to cache first
    log.info(f"Cache MISS: Downloading directory {remote_dir} to cache")
    _ensure_cache_dir(cache_dir)
    
    try:
        ctadata.fetch_and_save_dir(remote_dir, save_to_fn=str(cache_dir), recursive=True)
        
        # Copy from cache to requested local directory if different
        if cache_dir != local_dir:
            import shutil
            _ensure_cache_dir(local_dir)
            if local_dir.exists():
                shutil.rmtree(local_dir)
            shutil.copytree(cache_dir, local_dir)
        
        log.info(f"Successfully cached and saved directory to {local_dir}")
        return str(local_dir)
    
    except Exception as e:
        log.error(f"Failed to download directory {remote_dir}: {e}")
        # Clean up failed cache directory if it exists
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
        raise


def clear_cache(remote_path=None):
    """
    Clear the cache for a specific file/directory or the entire cache.
    
    Parameters
    ----------
    remote_path : str, optional
        If provided, clear cache only for this specific path.
        If None, clear the entire cache.
        
    Returns
    -------
    bool
        True if cache was cleared successfully
    """
    import shutil
    
    if remote_path is None:
        # Clear entire cache
        if CACHE_ROOT.exists():
            log.info(f"Clearing entire cache at {CACHE_ROOT}")
            shutil.rmtree(CACHE_ROOT)
            CACHE_ROOT.mkdir(parents=True, exist_ok=True)
            return True
        return False
    else:
        # Clear specific path
        cache_path = _remote_to_cache_path(remote_path)
        if cache_path.exists():
            log.info(f"Clearing cache for {remote_path}")
            if cache_path.is_file():
                cache_path.unlink()
            else:
                shutil.rmtree(cache_path)
            return True
        return False


def get_cache_info():
    """
    Get information about the cache.
    
    Returns
    -------
    dict
        Dictionary with cache statistics including:
        - cache_root: Path to cache root directory
        - total_files: Number of cached files
        - total_size: Total size in bytes
        - total_size_mb: Total size in MB
    """
    if not CACHE_ROOT.exists():
        return {
            "cache_root": str(CACHE_ROOT),
            "total_files": 0,
            "total_size": 0,
            "total_size_mb": 0.0,
        }
    
    total_files = 0
    total_size = 0
    
    for file_path in CACHE_ROOT.rglob("*"):
        if file_path.is_file():
            total_files += 1
            total_size += file_path.stat().st_size
    
    return {
        "cache_root": str(CACHE_ROOT),
        "total_files": total_files,
        "total_size": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
    }


@ensure_agent_running
def put_file(local_path, remote_path, update_cache=True):
    """
    Upload a file to dCache and optionally update the cache.
    
    Parameters
    ----------
    local_path : str
        Path to the local file to upload
    remote_path : str
        Destination path on dCache
    update_cache : bool, optional
        If True (default), also copy the file to cache for future retrieval
        
    Returns
    -------
    str
        Remote path where file was uploaded
    """
    local_path = Path(local_path)
    
    if not local_path.exists():
        raise FileNotFoundError(f"Local file {local_path} does not exist")
    
    if not local_path.is_file():
        raise ValueError(f"Local path {local_path} is not a file")
    
    try:
        # Upload to dCache
        log.info(f"Uploading {local_path} to {remote_path}")
        ctadata.upload_file(str(local_path), remote_path)
        
        # Update cache if requested
        if update_cache:
            cache_path = _remote_to_cache_path(remote_path)
            _ensure_cache_dir(cache_path)
            import shutil
            shutil.copy2(local_path, cache_path)
            log.info(f"Updated cache at {cache_path}")
        
        return remote_path
    
    except Exception as e:
        log.error(f"Failed to upload {local_path} to {remote_path}: {e}")
        raise


@ensure_agent_running
def put_dir(local_dir, remote_dir, update_cache=True):
    """
    Upload a directory to dCache and optionally update the cache.
    
    Parameters
    ----------
    local_dir : str
        Path to the local directory to upload
    remote_dir : str
        Destination path on dCache
    update_cache : bool, optional
        If True (default), also copy the directory to cache for future retrieval
        
    Returns
    -------
    str
        Remote directory path where files were uploaded
    """
    local_dir = Path(local_dir)
    
    if not local_dir.exists():
        raise FileNotFoundError(f"Local directory {local_dir} does not exist")
    
    if not local_dir.is_dir():
        raise ValueError(f"Local path {local_dir} is not a directory")
    
    try:
        # Upload to dCache
        log.info(f"Uploading directory {local_dir} to {remote_dir}")
        ctadata.upload_dir(str(local_dir), remote_dir, recursive=True)
        
        # Update cache if requested
        if update_cache:
            cache_dir = _remote_to_cache_path(remote_dir)
            _ensure_cache_dir(cache_dir)
            import shutil
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
            shutil.copytree(local_dir, cache_dir)
            log.info(f"Updated cache at {cache_dir}")
        
        return remote_dir
    
    except Exception as e:
        log.error(f"Failed to upload directory {local_dir} to {remote_dir}: {e}")
        raise