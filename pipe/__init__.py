"""Pipe.

A Python application for running subsea pipeline design calculations.
"""
import colorlog

__version__ = "0.1.0"

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(message)s"))

logger = colorlog.getLogger(__name__)
logger.addHandler(handler)

