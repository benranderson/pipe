# -*- coding: UTF-8 -*-

"""Main command line."""

import sys
import click
import toml
import os
from types import SimpleNamespace

from pipe import logger
from pipe.config import DEFAULT_INPUTDATA_FOLDER


@click.group()
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Print debug information, used for development",
)
@click.option(
    "--config",
    default=DEFAULT_INPUTDATA_FOLDER,
    help="Path to folder containing input data, defaults to input_data/",
)
@click.pass_context
def cli(ctx, debug, config):
    """
    \U00002705  Subsea pipeline design.

    To get started, run setup:

      $ pipe setup

    To determine the required wall thickness along the pipeline:

      $ pipe wall

    To determine the effective axial force along the pipeline:

      $ pipe buckle

    You can also graph results in a browser with:

      $ pipe graph <result>
    """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    if debug:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")


@cli.command()
@click.pass_context
def wall(ctx):
    """Calculate the minimum reqiured wall thickness."""

    from pipe.commands.cmd_wall import wall

    wall()


@cli.command()
@click.option("-p", "--plot/--no-plot", default=False, help="Plot results")
def buckle(plot):
    """Determine the effective axial force profile."""

    from pipe.commands.cmd_buckle import buckle

    buckle(plot)

