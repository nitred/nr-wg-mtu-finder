import argparse
import signal
import sys
import time

from pydantic import BaseModel, StrictStr

from nr_wg_mtu_finder.plot import create_heatmap_from_log


def signal_handler(sig, frame):
    """Handle ctrl+c interrupt.

    Without this handler, everytime a ctrl+c interrupt is received, the server shutdowns
    and proceeds to the next iteration in the loop rather than exiting the program
    altogether.
    """
    print("************Received CTRL-C. Will exit in 1 second************")
    time.sleep(1)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class ArgsModel(BaseModel):
    log_filepath: StrictStr
    heatmap_filepath: StrictStr

    class Config:
        orm_mode = True


def setup_args():
    """Setup args."""
    parser = argparse.ArgumentParser(
        description=(
            "nr-wg-mtu-finder-heatmap - "
            "Generate a heatmap file (png) from a log file (csv) that was created "
            "by the `nr-wg-mtu-finder` script. This is useful in case the original "
            "script file crashed midway."
        )
    )
    parser.add_argument(
        "--log-filepath",
        help=(
            "Absolute path to the log file (csv) that was created by the "
            "`nr-wg-mtu-finder` script."
        ),
        required=True,
    )
    parser.add_argument(
        "--heatmap-filepath",
        help=(
            "Absolute path to the heatmap file (png) which will be created from the "
            "log file (csv)."
        ),
        required=True,
    )
    args = parser.parse_args()
    return args


def run():
    args = setup_args()
    args = ArgsModel.from_orm(args)

    create_heatmap_from_log(
        log_filepath=args.log_filepath, heatmap_filepath=args.heatmap_filepath
    )
