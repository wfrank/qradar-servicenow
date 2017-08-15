__author__ = 'IBM'

from app import app
from app.qpylib import qpylib

qpylib.create_log()
app.run(debug = True, host='0.0.0.0')

