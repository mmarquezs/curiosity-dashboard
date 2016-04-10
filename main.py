import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
render_template, flash, jsonify,Response
from flask.ext.login import LoginManager
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from contextlib import closing
from pydbus import SystemBus
from werkzeug.debug import DebuggedApplication
import types

#CONFIG
DATABASE = "/tmp/flask-dashboard.db"
DEBUG = True
SECRET_KEY = 'devkey'
USERNAME = 'admin'
PASSWORD = 'admin'

#INITIALIZATION
app = Flask(__name__)
app.config.from_object(__name__)
app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
login_manager = LoginManager()
login_manager.init_app(app)
bootstrap = Bootstrap(app)

bus = SystemBus()
bus.timeout = -1
sysd = bus.get("org.freedesktop.systemd1")
sysd.get_unit = types.MethodType(lambda self,name: self._bus.get('.systemd1',self.LoadUnit(name)[0]), sysd)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route("/dashboard")
def main():
    return render_template('index.html')

@app.route("/dashboard/systemd")
def systemd_unit_list():
    units = sysd.ListUnits()[0]
    return jsonify({'data':units})

@app.route("/dashboard/service/<service_name>")
def service(service_name):
    return "Service: "+service_name

@app.route("/dashboard/systemd/<unit_name>/property/<property_>")
def systemd_property(unit_name,property_):
    return jsonify({'data':sysd.get_unit(unit_name).Get('org.freedesktop.systemd1.Unit',property_)[0]})

@app.route("/dashboard/systemd/<action>")
def systemd_action(action):
    method = getattr(sysd,action)
    app.logger.info("Function called: sysd."+action+"("+",".join([field for field in request.args])+")")
    return jsonify({'data':method(*[field for field in request.args])[0]})

@app.route("/dashboard/systemd/<unit_name>/<action>")
def systemd_unit_action(unit_name,action):
    """
    Calls an action (Get,Start,Stop,...) to a Service/Unit.
    """
    unit = sysd.get_unit(unit_name)
    method = getattr(unit,action)
    app.logger.info("Function called: unit."+action+"("+",".join([field for field in request.args])+")")
    return jsonify({'data':method(*[field for field in request.args])[0]})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
