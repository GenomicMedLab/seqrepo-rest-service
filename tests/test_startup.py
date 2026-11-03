"""Check local and Beanstalk startup and the merged refget routes."""

import os
import subprocess
import sys
from pathlib import Path

import connexion
import pytest

from seqrepo_rest_service import cli

SEQREPO_DIR = Path(__file__).parent / "data" / "seqrepo" / "master"
MD5 = "3332ed720ac7eaa9b3655c06f6b9e196"


@pytest.fixture
def local_app(monkeypatch):
    """Start through the local CLI without opening a listening socket."""
    applications = []

    def capture_run(application, **_kwargs):
        """Capture the application passed to the development server."""
        applications.append(application.app)

    monkeypatch.delenv("SEQREPO_EB_PROD", raising=False)
    monkeypatch.setattr(sys, "argv", ["seqrepo-rest-service", str(SEQREPO_DIR)])
    monkeypatch.setattr(connexion.App, "run", capture_run)

    cli.main()

    assert len(applications) == 1
    assert applications[0].config["seqrepo_dir"] == SEQREPO_DIR
    return applications[0]


def test_beanstalk_wsgi_import():
    """Gunicorn can import cli:app without command-line arguments."""
    env = dict(os.environ, SEQREPO_EB_PROD="true", SEQREPO_ROOT_DIR=str(SEQREPO_DIR.resolve()))
    script = (
        "from seqrepo_rest_service.cli import app; "
        "response = app.test_client().get('/seqrepo/1/ping'); "
        "assert response.status_code == 200, response.data"
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script], env=env, capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr


def test_local_cli_and_refget_metadata(local_app):
    """The local CLI serves the renamed metadata and service-info handlers."""
    client = local_app.test_client()

    metadata = client.get(f"/refget/1/sequence/{MD5}/metadata")
    service_info = client.get("/refget/1/sequence/service-info")

    assert metadata.status_code == 200
    assert metadata.json["metadata"]["md5"] == MD5
    assert service_info.status_code == 200
    assert service_info.json["service"]["algorithms"] == ["md5", "trunc512"]


@pytest.mark.parametrize(
    ("suffix", "headers", "status"),
    [
        ("?start=0&end=5", {}, 200),
        ("", {"Range": "bytes=0-4"}, 206),
    ],
    ids=["query-coordinates", "range-header"],
)
def test_refget_subsequence(local_app, suffix, headers, status):
    """Both coordinate forms return the requested slice after upstream's refactor."""
    client = local_app.test_client()

    response = client.get(f"/refget/1/sequence/{MD5}{suffix}", headers=headers)

    assert response.status_code == status
    assert response.get_data(as_text=True) == "GAGTT"
