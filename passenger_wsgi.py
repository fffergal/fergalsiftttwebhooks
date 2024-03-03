import datetime
import json
import logging
import logging.handlers
import os
import time
import traceback
from contextlib import closing
from urllib.parse import parse_qs
from urllib.request import Request, urlopen

LOGS_DIR = "logs"


class JSONLogFormatter(logging.Formatter):

    def __init__(self, datefmt=None):
        super().__init__(datefmt=datefmt)

    def format(self, record):
        attributes = {
            key: value for key, value in vars(record).items()
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
            attributes["exc_type"] = record.exc_info[0].__name__
            attributes["traceback"] = "".join(
                traceback.format_exception(
                    record.exc_info[0],
                    record.exc_info[1],
                    record.exc_info[2]
                )
            )
        except Exception:
            pass
        return json.dumps(attributes)


def wedding(environ, start_response):
    days = days_until(datetime.datetime.today(), datetime.datetime(2020, 10, 10))
    request = Request(
        "https://maker.ifttt.com/trigger/notify/with/key/dnaJW0wSYg5wScT5JZi-_o",
        f'{{"value1": "{days} days until wedding."}}',
        {"Content-type": "application/json"},
    )
    with closing(urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def debug(environ, start_response):
    if environ["REQUEST_METHOD"] != "POST":
        start_response("200 OK", [("Content-type", "application/json")])
        return [json.dumps(parse_qs(environ["QUERY_STRING"]), indent=2)]
    with closing(environ["wsgi.input"]) as request_body_file:
        request_body = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    start_response("200 OK", [("Content-type", "text/plain")])
    return [request_body]


def dropbox_debug(environ, start_response):
    if environ["REQUEST_METHOD"] != "POST":
        payload = json.dumps(parse_qs(environ["QUERY_STRING"]), indent=2)
    else:
        with closing(environ["wsgi.input"]) as request_body_file:
            payload = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    request = Request(
        "https://maker.ifttt.com/trigger/dropbox-debug/with/key/dnaJW0wSYg5wScT5JZi-_o",
        json.dumps(
            {"value1": payload}
        ),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def dropbox_log_route(environ, start_response):
    with closing(open(os.path.join(LOGS_DIR, "passenger.log"))) as log_file:
        log_content = log_file.read()
    request = Request(
        "https://maker.ifttt.com/trigger/dropbox-debug/with/key/dnaJW0wSYg5wScT5JZi-_o",
        json.dumps({"value1": log_content}),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def days_until_route(environ, start_response):
    if environ["REQUEST_METHOD"] != "POST":
        start_response("405 Method not allowed", [("Content-type", "text/plain")])
        return ["POST only please"]
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
        "https://maker.ifttt.com/trigger/notify/with/key/dnaJW0wSYg5wScT5JZi-_o",
        json.dumps(
            {
                "value1": f"{days} days until {target_label}.",
            }
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


def cleaning_from_gcal(environ, start_response):
    if environ["REQUEST_METHOD"] != "POST":
        start_response("405 Method not allowed", [("Content-type", "text/plain")])
        return ["POST only please"]
    with closing(environ["wsgi.input"]) as request_body_file:
        request_body = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    parsed_request = json.loads(request_body)
    gcal_datetime = parsed_request["datetime"]
    title = parsed_request["title"]
    trello_user = parsed_request["description"]
    parsed_datetime = datetime.datetime.strptime(gcal_datetime, GCAL_DATETIME_FORMAT)
    name = TRELLO_USERS_TO_NAMES[trello_user]
    telegram_request = Request(
        "https://maker.ifttt.com/trigger/telegram_afb/with/key/dnaJW0wSYg5wScT5JZi-_o",
        json.dumps(
            {
                "value1": f"{name}: {title}",
            }
        ),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(telegram_request)) as response:
        lines = list(response.readlines())
    trello_request = Request(
        "https://maker.ifttt.com/trigger/add_cleaning_trello/with/key/dnaJW0wSYg5wScT5JZi-_o",
        json.dumps(
            {
                "value1": f"{title} ({parsed_datetime:%a %d %b})",
                "value2": trello_user,
            }
        ),
        {"Content-type": "application/json"},
    )
    with closing(urlopen(trello_request)) as response:
        lines.extend(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def error_debug_route(environ, start_response):
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


def application(environ, start_response):
    route = routes.get(environ["PATH_INFO"])
    if not route:
        start_response("404 Not found", [("Content-type", "text/plain")])
        return ["Not found\n", environ["PATH_INFO"]]
    try:
        return route(environ, start_response)
    except Exception:
        try:
            if not os.path.exists(LOGS_DIR):
                os.makedirs(LOGS_DIR, 0o700)
            logger = logging.getLogger("fergalsiftttwebhooks")
            if not logger.handlers:
                handler = logging.handlers.TimedRotatingFileHandler(
                    os.path.join(LOGS_DIR, "passenger.log"),
                    when="D",
                    interval=1,
                    utc=True
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
                "Server error\n",
                "Problem logging error.\n",
                traceback.format_exc(),
            ]
        start_response("500 Server error", [("Content-type", "text/plain")])
        return ["Server error\n", "Errors logged."]


def days_until(date_from, date_to):
    return (date_to - date_from).days + 1
