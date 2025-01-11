import os
import sys

# setup app path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.append(app_dir)
os.chdir(app_dir)

from logger import enable_logger
enable_logger()

from dash_app import app
application = app.server
