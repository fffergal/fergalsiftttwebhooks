import ast
import datetime
import json
import logging
import logging.handlers
import os
import re
import time
import traceback
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import parse_qs
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from datetime import date

    from _typeshed.wsgi import StartResponse, WSGIEnvironment

# pyright: strict

LOGS_DIR = "logs"
LOG_FILE_NAME = "fergalsiftttwebhooks.log"


class JSONLogFormatter(logging.Formatter):
    def __init__(self, datefmt: str | None = None):
        super().__init__(datefmt=datefmt)

    def format(self, record: logging.LogRecord):
        attributes = {
            key: value
            for key, value in vars(record).items()
            if isinstance(value, str | int | float)
        }
        try:
            attributes["message"] = record.getMessage()
        except Exception:
            pass
        try:
            attributes["asctime"] = self.formatTime(record, datefmt=self.datefmt)
        except Exception:
            pass
        try:
            assert record.exc_info and record.exc_info[0] is not None
            attributes["exc_type"] = record.exc_info[0].__name__
            attributes["traceback"] = "".join(
                traceback.format_exception(
                    record.exc_info[0], record.exc_info[1], record.exc_info[2]
                )
            )
        except Exception:
            pass
        return json.dumps(attributes)


def wedding(environ: "WSGIEnvironment", start_response: "StartResponse") -> list[bytes]:
    days = days_until(datetime.datetime.today(), datetime.datetime(2020, 10, 10))
    request = Request(
        f"https://maker.ifttt.com/trigger/notify/with/key/{os.environ['IFTTT_WEBHOOK_KEY']}",
        bytes(f'{{"value1": "{days} days until wedding."}}', "utf-8"),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def debug(environ: "WSGIEnvironment", start_response: "StartResponse") -> list[bytes]:
    if environ["REQUEST_METHOD"] != "POST":
        start_response("200 OK", [("Content-type", "application/json")])
        return [bytes(json.dumps(parse_qs(environ["QUERY_STRING"]), indent=2), "utf-8")]
    with closing(environ["wsgi.input"]) as request_body_file:
        request_body = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    start_response("200 OK", [("Content-type", "text/plain")])
    return [request_body]


def dropbox_debug(
    environ: "WSGIEnvironment", start_response: "StartResponse"
) -> list[bytes]:
    if environ["REQUEST_METHOD"] != "POST":
        payload = json.dumps(parse_qs(environ["QUERY_STRING"]), indent=2)
    else:
        with closing(environ["wsgi.input"]) as request_body_file:
            payload = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    request = Request(
        f"https://maker.ifttt.com/trigger/dropbox-debug/with/key/{os.environ['IFTTT_WEBHOOK_KEY']}",
        bytes(json.dumps({"value1": payload}), "utf-8"),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def dropbox_log_route(
    environ: "WSGIEnvironment", start_response: "StartResponse"
) -> list[bytes]:
    log_content = (Path(LOGS_DIR) / LOG_FILE_NAME).read_text()
    request = Request(
        f"https://maker.ifttt.com/trigger/dropbox-debug/with/key/{os.environ['IFTTT_WEBHOOK_KEY']}",
        bytes(json.dumps({"value1": log_content}), "utf-8"),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def days_until_route(
    environ: "WSGIEnvironment", start_response: "StartResponse"
) -> list[bytes]:
    if environ["REQUEST_METHOD"] != "POST":
        start_response("405 Method not allowed", [("Content-type", "text/plain")])
        return [b"POST only please"]
    with closing(environ["wsgi.input"]) as request_body_file:
        request_body = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    parsed_request = json.loads(request_body)
    from_date = parsed_request["from_date"]
    target_date = parsed_request["target_date"]
    target_label = parsed_request["target_label"]
    parsed_from_date = datetime.datetime.strptime(from_date, "%B %d, %Y at %I:%M%p")
    parsed_target_date = datetime.datetime.strptime(target_date, "%Y-%m-%d")
    days = days_until(parsed_from_date, parsed_target_date)
    request = Request(
        f"https://maker.ifttt.com/trigger/notify/with/key/{os.environ['IFTTT_WEBHOOK_KEY']}",
        bytes(
            json.dumps(
                {
                    "value1": f"{days} days until {target_label}.",
                }
            ),
            "utf-8",
        ),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


GCAL_DATETIME_FORMAT = "%B %d, %Y at %I:%M%p"
TRELLO_USERS_TO_NAMES = {
    "@fffergal": "Fergal",
    "@annaarmstrong11": "Anna",
}


def cleaning_from_gcal(
    environ: "WSGIEnvironment", start_response: "StartResponse"
) -> list[bytes]:
    if environ["REQUEST_METHOD"] != "POST":
        start_response("405 Method not allowed", [("Content-type", "text/plain")])
        return [b"POST only please"]
    with closing(environ["wsgi.input"]) as request_body_file:
        request_body = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    parsed_request = json.loads(request_body)
    gcal_datetime = parsed_request["datetime"]
    title = parsed_request["title"]
    trello_user = parsed_request["description"]
    parsed_datetime = datetime.datetime.strptime(gcal_datetime, GCAL_DATETIME_FORMAT)
    name = TRELLO_USERS_TO_NAMES[trello_user]
    telegram_request = Request(
        f"https://maker.ifttt.com/trigger/telegram_afb/with/key/{os.environ['IFTTT_WEBHOOK_KEY']}",
        bytes(
            json.dumps(
                {
                    "value1": f"{name}: {title}",
                }
            ),
            "utf-8",
        ),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(telegram_request)) as response:
        lines = list(response.readlines())
    trello_request = Request(
        f"https://maker.ifttt.com/trigger/add_cleaning_trello/with/key/{os.environ['IFTTT_WEBHOOK_KEY']}",
        bytes(
            json.dumps(
                {
                    "value1": f"{title} ({parsed_datetime:%a %d %b})",
                    "value2": trello_user,
                }
            ),
            "utf-8",
        ),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(trello_request)) as response:
        lines.extend(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def error_debug_route(environ: "WSGIEnvironment", start_response: "StartResponse"):
    raise Exception


routes = {
    "/v1/wedding": wedding,
    "/v1/debug": debug,
    "/v1/dropbox-debug": dropbox_debug,
    "/v1/days-until": days_until_route,
    "/v1/error-debug": error_debug_route,
    "/v1/dropbox-log": dropbox_log_route,
    "/v1/cleaning-from-gcal": cleaning_from_gcal,
}


def application(environ: "WSGIEnvironment", start_response: "StartResponse"):
    route = routes.get(environ["PATH_INFO"])
    if not route:
        start_response("404 Not found", [("Content-type", "text/plain")])
        return [b"Not found\n", bytes(environ["PATH_INFO"], "utf-8")]
    try:
        return route(environ, start_response)
    except Exception:
        try:
            if not Path(LOGS_DIR).exists():
                os.makedirs(LOGS_DIR, 0o700)
            logger = logging.getLogger("fergalsiftttwebhooks")
            if not logger.handlers:
                handler = logging.handlers.TimedRotatingFileHandler(
                    Path(LOGS_DIR) / LOG_FILE_NAME,
                    when="D",
                    interval=1,
                    utc=True,
                )
                formatter = JSONLogFormatter()
                formatter.converter = time.gmtime
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            logger.exception(
                " - ".join([environ["PATH_INFO"], environ["REQUEST_METHOD"]])
            )
        except Exception:
            start_response("500 Server error", [("Content-type", "text/plain")])
            return [
                b"Server error\n",
                b"Problem logging error.\n",
                bytes(traceback.format_exc(), "utf-8"),
            ]
        start_response("500 Server error", [("Content-type", "text/plain")])
        return [b"Server error\n", b"Errors logged."]


def days_until(date_from: "date", date_to: "date"):
    return (date_to - date_from).days + 1


def parse_dot_env_gen(dot_env_content: str):
    for i, line in enumerate(dot_env_content.splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^export ([A-Z0-9_]+)=(.+)$", line)
        if not match:
            raise ValueError(f"Invalid line in dot env file {i}: {line}")
        try:
            value = ast.literal_eval(match[2])
            if not isinstance(value, str):
                value = match[2]
        except Exception:
            value = match[2]
        yield (match[1], value)


def parse_dot_env(dot_env_content: str):
    r"""
    Parse the content of a dot env file into a dict.

    The format is quite strict. Empty lines and lines starting with # are ignored. Lines
    must start with "export " and variable names must be all caps, numbers, and
    underscores. All values will be str because env vars can only be str. To make more
    complex str you can use a str literal (e.g. wrapped with quotes and with \n for new
    lines).
    """
    return dict(parse_dot_env_gen(dot_env_content))
