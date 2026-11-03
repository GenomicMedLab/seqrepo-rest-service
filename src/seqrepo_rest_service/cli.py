"""Start the SeqRepo REST service locally or through Elastic Beanstalk."""

import argparse
import importlib.resources
import logging
import os
import pathlib
import time

import coloredlogs
import connexion
from biocommons.seqrepo import SeqRepo
from flask import redirect

WAIT_POLL_PERIOD = 15

_logger = logging.getLogger(__name__)
resources = importlib.resources.files(__package__)


def _parse_opts():
    """Parse the local server's command-line arguments.

    :return: SeqRepo directory and path-waiting options.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "SEQREPO_INSTANCE_DIR",
        type=pathlib.Path,
        help="SeqRepo instance directory (e.g., /usr/local/share/seqrepo/2024-12-20)",
    )
    ap.add_argument(
        "--wait-for-path",
        "-w",
        action="store_true",
        default=False,
        help="Wait for path to exist before starting (useful for docker-compose)",
    )
    return ap.parse_args()


def _create_app():
    """Configure the APIs using Beanstalk environment variables or local arguments.

    :return: Connexion application and OpenAPI files to watch during development.
    """
    coloredlogs.install(level="INFO")

    if "SEQREPO_EB_PROD" in os.environ:
        seqrepo_dir = os.environ.get("SEQREPO_ROOT_DIR", "/usr/local/share/seqrepo/2024-12-20")
    else:
        for name in ("SEQREPO_DIR", "SEQREPO_ROOT_DIR"):
            if name in os.environ:
                _logger.warning("%s environment variable is now ignored", name)

        opts = _parse_opts()
        seqrepo_dir = opts.SEQREPO_INSTANCE_DIR
        if opts.wait_for_path:
            while not seqrepo_dir.exists():
                _logger.info("%s: waiting for existence", seqrepo_dir)
                time.sleep(WAIT_POLL_PERIOD)
            _logger.info("%s: path found", seqrepo_dir)
        _ = SeqRepo(seqrepo_dir.as_posix())

    cxapp = connexion.App(__name__, debug=True)
    cxapp.app.url_map.strict_slashes = False
    cxapp.app.config["seqrepo_dir"] = seqrepo_dir

    spec_files = []
    spec_fn = resources / "seqrepo" / "openapi.yaml"
    cxapp.add_api(str(spec_fn), validate_responses=True, strict_validation=True)
    spec_files += [spec_fn]

    @cxapp.route("/")
    @cxapp.route("/seqrepo")
    def seqrepo_ui():
        """Redirect to the SeqRepo API documentation.

        :return: Redirect response.
        """
        return redirect("/seqrepo/1/ui/")

    spec_fn = resources / "refget" / "refget-openapi.yaml"
    cxapp.add_api(str(spec_fn), validate_responses=True, strict_validation=True)
    spec_files += [spec_fn]

    @cxapp.route("/refget")
    def refget_ui():
        """Redirect to the refget API documentation.

        :return: Redirect response.
        """
        return redirect("/refget/1/ui/")

    _logger.info("Also watching %s", str(spec_files))
    return cxapp, spec_files


def main():
    """Configure and run the development server."""
    cxapp, spec_files = _create_app()
    cxapp.run(host="0.0.0.0", extra_files=spec_files)  # noqa: S104


# Gunicorn imports this WSGI object in the Elastic Beanstalk environment.
if "SEQREPO_EB_PROD" in os.environ:
    _cxapp, _spec_files = _create_app()
    app = _cxapp.app

if __name__ == "__main__":
    main()
