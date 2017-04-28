from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import 
import os

appname = "Vainglorious Meta"
app = Flask(__name__)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

app.config.from_object(os.environ.get("CONFIG_KEY"))

# app.config.from_object('config.ProductionConfig')
# app.config.from_envvar('YOURAPPLICATION_SETTINGS  ')
app.secret_key = 'anotherplaintextpasswordftw'

import models, views

#
# @app.teardown_request
# def teardown_request(exception=None):
#     print exception
