__author__ = 'ServiceNow Inc.'

import json
from flask import render_template, request, redirect, url_for
from app import app
from app.models.admin import SNConfiguration
from app.models.servicenow import ServiceNow


ServiceNow.start_auto_transmission_thread()


@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('admin'))


@app.route('/admin_screen', methods=['GET', 'POST'])
def admin():
    snconfig = SNConfiguration()
    snconfig.read_configuration()
    messages = []
    if request.method == 'POST':
        snconfig.merge_config_with_submitted_form(request.form)
        snconfig.save_configuration()
        messages.append('Configurations have been saved.')

    snconfig.read_configuration()
    return render_template('admin_screen.html', title='Admin Screen', form=snconfig.config, messages=messages)


@app.route('/get_sn_button_config', methods=['GET'])
def get_button_display_config():
    btn_config = {
        'show_event': False,
        'show_incident': False
    }
    snconfig = SNConfiguration()
    snconfig.read_configuration()
    if all((snconfig.config.get('instance_url', False),
            snconfig.config.get('username', False),
            snconfig.config.get('password', False))):
        btn_config = {
            'show_event': snconfig.config.get('show_event_button', False),
            'show_incident': snconfig.config.get('show_incident_button', False)
        }
    return json.dumps(btn_config)


@app.route('/offense_to_sn_incident', methods=['GET'])
def send_offense_as_incident():
    resp = _send_offense()
    return json.dumps(resp)


@app.route('/offense_to_sn_event', methods=['GET'])
def send_offense_as_event():
    resp = _send_offense(True)
    return json.dumps(resp)


def _send_offense(as_event=False):
    offense_id = request.args.get('context')
    snconfig = SNConfiguration()
    snconfig.read_configuration()
    snow = ServiceNow(snconfig.config)
    if as_event:
        return snow.create_security_event(offense_id)
    else:
        return snow.create_security_incident(offense_id)
