"""
Carry out pipeline wall thickness calculations
"""

from pipe import logger


def calc_wall():
    return 5


def wall():
    """Calculate the minimum reqiured wall thickness."""

    w = calc_wall()

    logger.info(
        f"Wall Thickness: {w} mm\n"
        "Completed wall thickness calculation, run `wily graph wall` to view results."
    )
