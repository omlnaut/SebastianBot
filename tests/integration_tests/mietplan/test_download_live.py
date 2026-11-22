"""`seadepot download` against the live webdepot.

Skipped cleanly without `SEAMIETPLAN_CREDENTIALS`. The unit suite never reaches
the portal; this is the one place a real document is resolved and written.
"""

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Sequence

import pytest

from cli.mietplan import run
from sebastian.clients.mietplan.client.client import MietplanClient


def _run(
    client: MietplanClient, argv: Sequence[str]
) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = run(argv, client)
    return code, out.getvalue(), err.getvalue()


def _payload(client: MietplanClient, argv: Sequence[str]) -> dict[str, Any]:
    code, out, err = _run(client, argv)
    assert code == 0, err
    payload: dict[str, Any] = json.loads(out)
    return payload


def test_download_writes_a_real_document_under_out(
    mietplan_client: MietplanClient, tmp_path: Path
):
    found = _payload(mietplan_client, ["search", "--limit", "1"])
    if not found["files"]:
        pytest.skip("the webdepot currently holds no files to download")
    portal_path = found["files"][0]["path"]
    out_dir = tmp_path / "downloads"

    result = _payload(
        mietplan_client, ["download", portal_path, "--out", str(out_dir)]
    )

    assert result["command"] == "download"
    assert result["path"] == portal_path
    written = Path(result["file"]["path"])
    assert written.is_absolute()
    assert written.is_relative_to(out_dir.resolve())
    assert written.is_file()
    content = written.read_bytes()
    assert content
    assert len(content) == result["file"]["bytes"]
