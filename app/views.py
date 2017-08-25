from flask import render_template, request, redirect, url_for, jsonify, make_response

from app import app
from app.models.admin import ServiceNowConfiguration
from app.models.servicenow import ServiceNow


ServiceNow.start_auto_sync_thread()


@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('admin'))


@app.route('/admin_screen', methods=['GET', 'POST'])
def admin():
    snconfig = ServiceNowConfiguration()
    snconfig.read_configuration()
    messages = []
    if request.method == 'POST':
        snconfig.merge_config_with_submitted_form(request.form)
        snconfig.save_configuration()
        messages.append('Configurations have been saved.')

    snconfig.read_configuration()
    return render_template('admin_screen.html', title='Admin Screen', form=snconfig.config, messages=messages)


@app.route('/preview/<int:offense_id>', methods=['GET'])
def preview_incident(offense_id):
    offense_id = str(offense_id)
    snconfig = ServiceNowConfiguration()
    snconfig.read_configuration()
    snow = ServiceNow(snconfig.config)
    incident = snow.preview_incident(offense_id)
    return render_template('preview.html', title='Incident Preview', config=snconfig.config, incident=incident)


@app.route('/submit/<int:offense_id>', methods=['POST'])
def submit_incident(offense_id):
    offense_id = str(offense_id)
    updates = request.get_json()
    snconfig = ServiceNowConfiguration()
    snconfig.read_configuration()
    snow = ServiceNow(snconfig.config)
    result = snow.submit_incident(offense_id, updates)
    return jsonify(result)
