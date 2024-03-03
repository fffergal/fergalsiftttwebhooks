# This file contains the WSGI configuration required to serve up your
# web application at http://ifttt.bfot.co.uk/
# It works by setting the variable 'application' to a WSGI handler of some
# description.


# +++++++++++ GENERAL DEBUGGING TIPS +++++++++++
# getting imports and sys.path right can be fiddly!
# We've tried to collect some general tips here:
# https://help.pythonanywhere.com/pages/DebuggingImportError

# +++++++++++ VIRTUALENV +++++++++++
# If you want to use a virtualenv, set its path on the web app setup tab.
# Then come back here and import your application object as per the
# instructions below.

import sys

path = "/home/fffergaleu/path/to/my/app"
if path not in sys.path:
    sys.path.append(path)

from fergalsiftttwebhooks import application  # noqa
