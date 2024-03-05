import functools
import os
import signal
import threading
import time
import wsgiref.simple_server
from pathlib import Path
from typing import TYPE_CHECKING

import fergalsiftttwebhooks

if TYPE_CHECKING:
    import types
    from collections.abc import Callable
    from typing import Any

# pyright: strict


def stop_serving(
    app_server: wsgiref.simple_server.WSGIServer,
    old_sigint_handler: "Callable[[int, types.FrameType | None], Any] | int | signal.Handlers | None",
    signalnum: "int | signal.Signals",
    frame: "types.FrameType | None",
):
    print("Stopping")
    app_server.shutdown()
    signal.signal(signal.SIGINT, old_sigint_handler)


def main():
    try:
        os.environ.update(
            fergalsiftttwebhooks.parse_dot_env(
                (Path(fergalsiftttwebhooks.__file__).parent / ".env").read_text()
            )
        )
    except Exception:
        pass
    app_server = wsgiref.simple_server.make_server(
        "127.0.0.1",
        8000,
        fergalsiftttwebhooks.application,
    )
    old_sigint_handler = signal.getsignal(signal.SIGINT)

    signal.signal(
        signal.SIGINT, functools.partial(stop_serving, app_server, old_sigint_handler)
    )
    server_thread = threading.Thread(target=app_server.serve_forever)
    print("Started on port 8000")
    server_thread.start()
    while server_thread.is_alive():
        time.sleep(0.4)
    app_server.server_close()
    print("Stopped")


if __name__ == "__main__":
    main()
