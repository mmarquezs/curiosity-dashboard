import sqlite3
import os
from flask import Flask, request, session, g, redirect, url_for, abort, \
render_template, flash, jsonify,Response
from flask.ext.login import LoginManager
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.mail import Mail
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from contextlib import closing
from pydbus import SystemBus
from werkzeug.debug import DebuggedApplication
import types
basedir = os.path.abspath(os.path.dirname(__file__))

#CONFIG

DEBUG = True
SECRET_KEY = 'devkey'
USERNAME = 'admin'
PASSWORD = 'admin'
SQLALCHEMY_DATABASE_URI = 'sqlite:///'+os.path.join(basedir,'data.sqlite')
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = ""
MAIL_PASSWORD = ""
DASHBOARD_MAIL_SUBJECT_PREFIX = "[Dashboard-Curiosity]"
DASHBOARD_MAIL_SENDER = "Admin <mmsa1994@gmail.com>"

#INITIALIZATION
app = Flask(__name__)
app.config.from_object(__name__)
app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
login_manager = LoginManager()
login_manager.init_app(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
mail = Mail(app)

bus = SystemBus()
bus.timeout = -1
sysd = bus.get("org.freedesktop.systemd1")
sysd.get_unit = types.MethodType(lambda self,name: self._bus.get('.systemd1',self.LoadUnit(name)[0]), sysd)

def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    mail.send(msg)

#DATABASE MODEL
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    password = db.Column(db.String(20))
    email = db.Column(db.String(64), unique=True)
    first_name = db.Column(db.String(20))
    surname1 = db.Column(db.String(20))
    surname2 = db.Column(db.String(20), nullable=True)
    show_all_services = db.Column(db.Boolean, default=True)
    enabled_services = db.relationship('Services_enabled', backref='user', cascade="delete", order_by="desc(Services_enabled.service_id)")

    def __repr__(self):
        return '<User %r>' % self.username

class Services_enabled(db.Model):
    __tablename__ = 'services_enabled'
    service_id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    shown = db.Column(db.Boolean, default=True)
    custom_name = db.Column(db.String(10), nullable=True)
    def __repr__(self):
        return '<User %r | Service %r : %r>' % (self.user_id,self.service_id,self.shown)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    users = db.relationship("User", backref="role")

    def __repr__(self):
        return '<Role %r>' % self.name

@app.route("/dashboard")
def main():
    return render_template('index.html')



@app.route("/dashboard/services")
def services():
    services = sysd.ListUnits()[0]
    new_services_list = []
    for service in services :
        if service[0].split('.')[-1]=="service":
            name = "".join(service[0].split('.')[:-1]).replace("-"," ")
            filename = service[0]
            desc = service[1]
            status = service[4]
            new_services_list += [{
                "name" : name,
                "filename" : filename,
                "status" : status,
                "desc" : desc,
                "status" : status,
            }]
    return render_template('services.html',services=new_services_list)
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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

if __name__ == "__main__":
    manager.run()
    # app.run(host='0.0.0.0', port=8080)
