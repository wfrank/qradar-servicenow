__author__ = 'ServiceNow Inc.'

import atexit
import requests
import json
import sys
import traceback
from app.models.admin import SNConfiguration
from app.models.crypto import SNCrypto
from app.models.qradar import QRadar, QRadarDataClient
from app.qpylib import qpylib
from jinja2 import Template, TemplateError
from requests.compat import urljoin, quote_plus
from threading import Event, Thread


class ServiceNow(object):
    def __init__(self, config, use_svc_token=False):
        self.client = ServiceNowDataClient(config)
        self.config = config
        if use_svc_token:
            self.qradar = QRadar(QRadarDataClient(token=self.config['svc_account_token'], csrf=' '))
        else:
            self.qradar = QRadar(QRadarDataClient())

    @staticmethod
    def start_auto_transmission_thread():
        ctrl_event = Event()

        def handle_auto_transmission():
            while not ctrl_event.is_set():
                snconfig = SNConfiguration()
                try:
                    snconfig.read_configuration()
                    ctrl_event.wait(snconfig.config.get("filter_check_frequency_seconds", 90))
                    if not all((snconfig.config.get('instance_url', False),
                                snconfig.config.get('username', False),
                                snconfig.config.get('password', False),
                                snconfig.config.get('svc_account_token', False),
                                ((snconfig.config.get('auto_create_incidents')
                                  and snconfig.config.get('incident_filter'))
                                 or (snconfig.config.get('auto_create_events')
                                     and snconfig.config.get('event_filter'))))):
                        continue
                    qpylib.log("Checking for offenses")
                    sn = ServiceNow(snconfig.config, use_svc_token=True)
                    current_max = sn.qradar.get_max_offense_id(snconfig.config.get('last_max', 0))
                    inc = sn.create_security_incidents(current_max)
                    evt = sn.create_security_events(current_max)
                    snconfig.read_configuration()
                    snconfig.config['last_max'] = current_max
                    snconfig.save_configuration()
                    if inc is not None and len(inc):
                        qpylib.log("Sent over {0} incidents".format(len(inc)))
                    else:
                        qpylib.log("No incidents sent")
                    if evt is not None and len(evt):
                        qpylib.log("Sent over {0} events".format(len(evt)))
                    else:
                        qpylib.log("No events sent")
                except:
                    qpylib.log("Caught exception checking for offenses: " + str(sys.exc_info()[0]))
                    qpylib.log(traceback.format_exc())
        threadder = Thread(target=handle_auto_transmission)
        threadder.daemon = True

        def stop_auto_transmission():
            ctrl_event.set()

        atexit.register(stop_auto_transmission)
        threadder.start()

    def create_security_incidents(self, current_max=0):
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

    def create_security_incident(self, offense_id):
        offense = self.qradar.get_offense_graph(offense_id)
        return self._send_incident_and_add_note(offense)

    def create_security_events(self, current_max=0):
        evt = []
        last_max = self.config.get("last_max", current_max)
        delta_filter = "id > " + str(int(last_max)) + " and id <= " + str(current_max)
        if not self.config.get('auto_create_events', False) or not self.config.get("event_filter"):
            return None
        inc_filter = delta_filter + " and ({0})".format(self.config.get("event_filter"))
        offenses = self.qradar.get_offense_graphs(inc_filter)
        if offenses is None:
            return
        for offense in offenses:
            evt.append(self._send_event_and_add_note(offense))
        return evt

    def create_security_event(self, offense_id):
        offense = self.qradar.get_offense_graph(offense_id)
        return self._send_event_and_add_note(offense)

    def _send_incident_and_add_note(self, offense):
        if not self._precheck_configs():
            return {
                'is_error': True,
                'url': None,
                'error': "Please configure the ServiceNow integration",
                'raw': None
            }
        offense_id = offense['id']
        incident_data = self._to_security_incident(offense)
        resp = self.client.send_incident(incident_data)
        is_error = resp is None or resp['result'] is None or resp['result'][0] is None or resp['result'][0]['sys_id'] is None
        url = None
        error = None
        if not is_error:
            url = self._build_sn_url('sn_si_incident', resp['result'][0]['sys_id'])
        else:
            error = 'Encountered error creating Security Incident in ServiceNow'
        ret_obj = {
            'is_error': is_error,
            'url': url,
            'error': error,
            'raw': resp
        }
        if url is not None and not is_error:
            msg = 'Sent offense to ServiceNow as a security incident. The ServiceNow record URL is {0}' \
                .format(ret_obj['url'])
            self.qradar.post_offense_note(offense_id, msg)
        return ret_obj

    def _send_event_and_add_note(self, offense):
        if not self._precheck_configs():
            return {
                'is_error': True,
                'url': None,
                'error': "Please configure the ServiceNow integration",
                'raw': None
            }
        event_data = self._to_security_event(offense)
        resp = self.client.send_event(event_data)
        is_error = resp is None or resp['result'] is None or resp['result']['sys_id'] is None
        url = None
        error = None
        if not is_error:
            url = self._build_sn_url('em_event', resp['result']['sys_id'])
        else:
            error = 'Encountered error creating event in ServiceNow'
        ret_obj = {
            'is_error': is_error,
            'url': url,
            'error': error,
            'raw': resp
        }
        if url is not None and not is_error:
            msg = 'Sent offense to ServiceNow as an event. The ServiceNow record URL is {0}' \
                .format(ret_obj['url'])
            self.qradar.post_offense_note(offense['id'], msg)
        return ret_obj

    def _build_sn_url(self, table, sys_id):
        end = quote_plus("{0}.do?sys_id={1}".format(table, sys_id))
        return urljoin(self.config['instance_url'], '/nav_to.do?uri=' + end)

    def _to_security_incident(self, offense):
        drilldown = 'https://{0}/console/qradar/jsp/QRadar.jsp?appName=Sem&pageId=OffenseSummary&summaryId={1}'\
            .format(qpylib.get_console_address(), offense['id'])
        incident_map = {
            'contact_type': 'siem',
            'correlation_id': offense['id'],
            'correlation_display': 'QRadar',
            'external_url': drilldown
        }
        for key, value in self.config['incident_offense_map'].iteritems():
            tpl = Template(value)
            try:
                formatted = tpl.render(offense=offense)
            except TemplateError:
                qpylib.log('Encountered error parsing QRadar value for key: {0}'.format([key]))
                formatted = ''
            incident_map[key] = formatted

        return incident_map

    def _to_security_event(self, offense):
        event_map = {
            'classification': '1',
            'source': 'QRadar'
        }
        for key, value in self.config['event_offense_map'].iteritems():
            tpl = Template(value)
            try:
                formatted = tpl.render(offense=offense)
            except TemplateError:
                qpylib.log('Encountered error parsing QRadar value for key: {0}'.format([key]))
                formatted = ''
            event_map[key] = formatted
        if 'additional_info' not in event_map:
            event_map['additional_info'] = json.dumps(self._to_security_incident(offense))
        return event_map

    def _precheck_configs(self):
        return all((self.config.get('instance_url', False),
                    self.config.get('username', False),
                    self.config.get('password', False)))


class ServiceNowDataClient(object):
    def __init__(self, config):
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.config = config
        self.base_url = config['instance_url']

    def send_incident(self, field_mapping):
        path = '/api/now/import/sn_si_incident_import'
        return self._do_post(path, field_mapping)

    def send_event(self, field_mapping):
        path = '/api/now/table/em_event'
        return self._do_post(path, field_mapping)

    def _do_post(self, path, data):
        crypto = SNCrypto()
        config = SNConfiguration()
        url = urljoin(self.config['instance_url'], path)
        user = self.config.get('username', '')
        pwd = self.config.get('password', '')
        if pwd:
            pwd = crypto.decrypt(pwd, config.get_key())
        proxy_user = self.config.get('proxy_username', '')
        proxy_password = self.config.get('proxy_password', '')
        if proxy_password:
            proxy_password = crypto.decrypt(proxy_password, config.get_key())
        proxy_url = self.config.get('proxy_url', '')
        proxy_url = proxy_url.strip()
        accept_all = self.config.get('accept_all_certs', False)
        verify = not accept_all
        if proxy_url:
            if "://" not in proxy_url:
                proxy_url = "http://{0}".format(proxy_url)
            if proxy_user and proxy_password:
                proxy_url = proxy_url\
                    .replace("://", "://{0}:{1}@")\
                    .format(proxy_user, proxy_password)
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }

            resp = requests.request('POST', url, json=data, proxies=proxies,
                                    headers=self.headers, auth=(user, pwd), verify=verify)
        else:
            resp = requests.request('POST', url, json=data,
                                    headers=self.headers, auth=(user, pwd), verify=verify)

        if resp.status_code < 200 or resp.status_code > 300:
            qpylib.log('Encountered unsuccessful response code: {0}'
                       .format(resp.status_code))
            return None

        return resp.json()
