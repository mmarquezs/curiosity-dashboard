from flask import Flask,request,jsonify
# from dbus import SystemBus,Interface
from pydbus import SystemBus
import types
app = Flask(__name__)
bus = SystemBus()
sysd = bus.get("org.freedesktop.systemd1")
sysd.get_unit = types.MethodType(lambda self,name: self._bus.get('.systemd1',self.LoadUnit(name)[0]), sysd)

@app.route("/dashboard")
def main():
    return "Hello World!"

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
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
