import json
import logging
import threading
import time
import wsgiref.simple_server
from contextlib import closing
from datetime import datetime
from urllib.request import urlopen

import pytest

import fergalsiftttwebhooks


def test_days_until():
    assert (
        fergalsiftttwebhooks.days_until(datetime(2018, 1, 13, 6, 0), datetime(2018, 1, 15))
        == 2
    )


@pytest.fixture
def logger(tmpdir):
    logger = logging.getLogger("testlogger")
    handler = logging.FileHandler(str(tmpdir / "log.txt"))
    formatter = fergalsiftttwebhooks.JSONLogFormatter()
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)
    handler.close()


def test_jsonlogformatter(logger, tmpdir):
    logger.error("test %s", "yo")
    assert json.load(tmpdir / "log.txt")["message"] == "test yo"


@pytest.fixture
def server():
    app_server = wsgiref.simple_server.make_server(
        "127.0.0.1",
        8000,
        fergalsiftttwebhooks.application,
    )
    serve_thread = threading.Thread(target=app_server.serve_forever)
    serve_thread.start()
    yield
    app_server.shutdown()
    serve_thread.join(1.0)
    if serve_thread.is_alive():
        raise Exception("Server thread could not be stopped.")
    app_server.server_close()


def test_debug(server):
    response = urlopen("http://127.0.0.1:8000/v1/debug?hey=yo", None, 1)
    with closing(response) as response_body:
        assert json.loads(str(response_body.read(), "utf-8")) == {"hey": ["yo"]}
