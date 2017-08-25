import atexit
import sys
import traceback

import requests
from app.models.admin import ServiceNowConfiguration
from app.models.crypto import CryptoUtils
from app.models.qradar import QRadar, QRadarClient
from app.qpylib import qpylib
from jinja2 import Template, TemplateError
from requests.compat import urljoin, quote_plus
from threading import Event, Thread


class ServiceNow(object):
    def __init__(self, config, use_svc_token=False):
        self.client = ServiceNowClient(config)
        self.config = config
        if use_svc_token:
            self.qradar = QRadar(QRadarClient(token=self.config['svc_account_token'], csrf=' '))
        else:
            self.qradar = QRadar(QRadarClient())

    @staticmethod
    def start_auto_sync_thread():
        ctrl_event = Event()

        def handle_auto_sync():
            while not ctrl_event.is_set():
                snconfig = ServiceNowConfiguration()
                snconfig.read_configuration()
                ctrl_event.wait(snconfig.config.get("auto_sync_frequency", 60))
                if not all((snconfig.config.get('instance_url', False),
                            snconfig.config.get('username', False),
                            snconfig.config.get('password', False),
                            snconfig.config.get('svc_account_token', False),
                            )): continue
                if snconfig.config.get('auto_create_incidents') and snconfig.config.get('incident_filter'):
                    try:
                        qpylib.log("Checking for new offenses in QRadar")
                        sn = ServiceNow(snconfig.config, use_svc_token=True)
                        current_max = sn.qradar.get_max_offense_id(snconfig.config.get('last_max', 0))
                        inc = sn.create_incidents(current_max)
                        snconfig.read_configuration()
                        snconfig.config['last_max'] = current_max
                        snconfig.save_configuration()
                        if inc is not None and len(inc):
                            qpylib.log("Created {0} incidents".format(len(inc)))
                        else:
                            qpylib.log("No incidents created")
                    except:
                        qpylib.log("Caught exception creating incidents: " + str(sys.exc_info()[0]))
                        qpylib.log(traceback.format_exc())
                if snconfig.config.get('auto_close_offenses'):
                    try:
                        qpylib.log("Checking for incidents recently closed in ServiceNow")
                        sn = ServiceNow(snconfig.config, use_svc_token=True)
                        closed_incidents = sn.get_resolved_incidents()
                        offenses_closed = sn.qradar.close_offenses(closed_incidents)
                        if offenses_closed is not None and len(offenses_closed):
                            qpylib.log("Closed {0} offenses".format(len(offenses_closed)))
                        else:
                            qpylib.log("No offenses closed")
                    except:
                        qpylib.log("Caught exception closing offenses: " + str(sys.exc_info()[0]))
                        qpylib.log(traceback.format_exc())

        threadder = Thread(target=handle_auto_sync)
        threadder.daemon = True

        def stop_auto_sync():
            ctrl_event.set()

        atexit.register(stop_auto_sync)
        threadder.start()

    def create_incidents(self, current_max=0):
        inc = []
        last_max = self.config.get("last_max", current_max)
        delta_filter = "id > " + str(int(last_max)) + " and id <= " + str(current_max)
        if not self.config.get('auto_create_incidents', False) or not self.config.get("incident_filter"):
            return None
        inc_filter = delta_filter + " and ({0})".format(self.config.get("incident_filter"))
        offenses = self.qradar.get_offense_graphs(inc_filter)
        if offenses is None:
            return
        for offense in offenses:
            inc.append(self._send_incident_and_add_note(offense))
        return inc

    def create_incident(self, offense_id):
        offense = self.qradar.get_offense_graph(offense_id)
        return self._send_incident_and_add_note(offense)

    def preview_incident(self, offense_id):
        offense = self.qradar.get_offense_graph(offense_id)
        return self._to_security_incident(offense)

    def submit_incident(self, offense_id, updates):
        offense = self.qradar.get_offense_graph(offense_id)
        for k, v in updates.items():
            offense[k] = v
        return self._send_incident_and_add_note(offense)

    def _send_incident_and_add_note(self, offense):
        if not self._precheck_configs():
            return {
                'is_error': True,
                'record': None,
                'url': None,
                'error': "Please configure the ServiceNow integration",
                'raw': None
            }
        incident_data = self._to_security_incident(offense)
        resp = self.client.send_incident(incident_data)
        is_error = resp is None or resp['result'] is None or resp['result']['sys_id'] is None
        record = None
        url = None
        error = None
        if not is_error:
            record = resp['result']['number']
            url = self._build_sn_url('incident', resp['result']['sys_id'])
        else:
            error = 'Encountered error creating incident in ServiceNow'
        ret_obj = {
            'is_error': is_error,
            'record': record,
            'url': url,
            'error': error,
            'raw': resp
        }
        if record is not None and url is not None and not is_error:
            msg = '''Sent offense to ServiceNow as an incident.

                     Incident ID: {0}
                     Incident URL: {1}
                  '''.format(record, url)
            self.qradar.post_offense_note(offense['id'], msg)
        return ret_obj

    def _build_sn_url(self, table, sys_id):
        end = quote_plus("{0}.do?sys_id={1}".format(table, sys_id))
        return urljoin(self.config['instance_url'], '/nav_to.do?uri=' + end)

    def _to_security_incident(self, offense):
        offense_url = 'https://{0}/console/qradar/jsp/QRadar.jsp?appName=Sem&pageId=OffenseSummary&summaryId={1}' \
            .format(qpylib.get_console_address(), offense['id'])
        incident_map = {
            'contact_type': 'siem',
            'correlation_id': offense['id'],
            'correlation_display': 'QRadar',
            'external_url': offense_url
        }
        for key, value in self.config['offense_map'].iteritems():
            tpl = Template(value)
            try:
                formatted = tpl.render(offense=offense)
            except TemplateError:
                qpylib.log('Encountered error parsing QRadar value for key: {0}'.format([key]))
                formatted = ''
            incident_map[key] = formatted
        return incident_map

    def _precheck_configs(self):
        return all((self.config.get('instance_url', False),
                    self.config.get('username', False),
                    self.config.get('password', False)))

    def get_resolved_incidents(self):
        params = {
            "sysparm_query": "sys_created_by=qradar^incident_state=6",
            "sysparm_fields": "number,correlation_id,resolved_at,u_resolution_code,close_notes"
        }
        return self.client.search_incidents(params)


class ServiceNowClient(object):
    def __init__(self, config):
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.config = config
        self.base_url = config['instance_url']

    def search_incidents(self, params):
        path = '/api/now/table/incident'
        return self._do_http('GET', path, params=params)["result"]

    def send_incident(self, field_mapping):
        path = '/api/now/table/incident'
        return self._do_http('POST', path, json=field_mapping)

    def _do_http(self, method, path, **kwargs):
        options = kwargs
        crypto = CryptoUtils()
        config = ServiceNowConfiguration()
        url = urljoin(self.config['instance_url'], path)
        user = self.config.get('username', '')
        pwd = self.config.get('password', '')
        if pwd:
            pwd = crypto.decrypt(pwd, config.get_key())
        options["auth"] = (user, pwd)

        proxy_user = self.config.get('proxy_username', '')
        proxy_password = self.config.get('proxy_password', '')
        if proxy_password:
            proxy_password = crypto.decrypt(proxy_password, config.get_key())
        proxy_url = self.config.get('proxy_url', '')
        proxy_url = proxy_url.strip()
        if proxy_url:
            if "://" not in proxy_url:
                proxy_url = "http://{0}".format(proxy_url)
            if proxy_user and proxy_password:
                proxy_url = proxy_url.replace("://", "://{0}:{1}@").format(proxy_user, proxy_password)

            options["proxies"] = {
                "http": proxy_url,
                "https": proxy_url
            }
        options["verify"] = not self.config.get('accept_all_certs', False)

        resp = requests.request(method, url, **options)

        if resp.status_code < 200 or resp.status_code > 300:
            qpylib.log('Encountered unsuccessful response code: {0}'
                       .format(resp.status_code))
            return None

        return resp.json()
