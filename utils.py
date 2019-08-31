import os
import pickle
from functools import wraps
from datetime import datetime
from loguru import logger


def calc_timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        elapsed = datetime.now()-start
        logger.debug("CT: {} -- {}".format(func.__name__, elapsed))
        return result
    return wrapper


def cached(func):
    func.cache = {}
    @wraps(func)
    def wrapper(*args):
        try:
            return func.cache[args]
        except KeyError:
            func.cache[args] = result = func(*args)
            return result
    return wrapper


def load_cache(func):

    if hasattr(func, "cache"):
        try:
            filename = os.path.join("/tmp", "_cache_%s" % (func.__name__))
            with open(filename, 'rb') as fh:
                func.__wrapped__.cache = pickle.load(fh)
            logger.debug(
                "loaded {} objects for {}".format(
                    len(func.__wrapped__.cache), func.__name__
                )
            )
            # logger.debug(pformat(func.__wrapped__.cache))
        except FileNotFoundError:
            logger.warning(f"no cache file {filename} found (yet?)")
    else:
        logger.warning(f"{func.__name__} is not cacheable.")


def save_cache(func):
    if hasattr(func, "cache"):
        filename = "_cache_%s" % (func.__name__)
        filename = os.path.join("/tmp", "_cache_%s" % (func.__name__))
        # logger.debug(pformat(func.__wrapped__.cache))
        logger.debug(
            "saving {} objects for {}".format(
                len(func.__wrapped__.cache), func.__name__
            )
        )
        with open(filename, 'wb') as fh:
            pickle.dump(func.__wrapped__.cache, fh)
    else:
        logger.warning(f"{func.__name__} is not cacheable.")
