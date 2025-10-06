# -*- coding: utf-8 -*-
import logging
import sys


def _ensure_root_configured(level=logging.INFO):
    root = logging.getLogger()
    if getattr(_ensure_root_configured, "_done", False):
        return
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        root.addHandler(handler)
    root.setLevel(level)
    _ensure_root_configured._done = True


def get_logger(name, level=logging.INFO):
    _ensure_root_configured(level)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
