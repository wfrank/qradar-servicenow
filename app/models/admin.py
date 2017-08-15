__author__ = 'ServiceNow Inc.'

import json
import os
import copy
from app.models.crypto import SNCrypto

from app.qpylib import qpylib


class SNConfiguration(object):
    filename = os.path.join(qpylib.get_store_path(),
                            'snow_config.json')
    _keyfile = os.path.join(qpylib.get_store_path(), 'shhh.txt')

    def __init__(self):
        """ Initial Config """
        self.config = {
            'instance_url': '',
            'username': '',
            'password': '',
            'svc_account_token': '',
            'incident_offense_map': {
                'short_description': 'QRadar-{{ offense.id }} - {{ offense.description }}',
                'description': 'QRadar-{{ offense.id }} - {{ offense.description }}',
                'cmdb_ci': '{{ offense.local_destination_addresses[0].local_destination_ip }}',
                'severity': '{{ 3 - (offense.severity /10 * 2)|round|int }}',
                'source_ip': '{{ offense.source_addresses[0].source_ip }}',
                'dest_ip': '{{ offense.local_destination_addresses[0].local_destination_ip }}'
            },
            'event_offense_map': {
                'node': '{{ offense.local_destination_addresses[0].local_destination_ip }}',
                'type': '{{ offense.offense_type_name }}',
                'resource': 'QRADAR-EVENT-OFFENSE-{{ offense.id }}',
                'severity': '{{ 5 - (offense.severity /10 * 4)|round|int }}',
                'description': 'QRadar-{{ offense.id }} - {{ offense.description }}'
            },
            'auto_create_incidents': False,
            'auto_create_events': False,
            'filter_check_frequency_seconds': 90,
            'event_filter': '',
            'incident_filter': '',
            'proxy_url': '',
            'proxy_username': '',
            'proxy_password': '',
            'accept_all_certs': False,
            'show_event_button': True,
            'show_incident_button': True,
        }
        self._key = None

    def get_key(self):
        if not os.path.isfile(self._keyfile):
            self._create_key_file()
        self._key = self._read_key_file()
        if self._key is None:
            self._create_key_file()
        self._key = self._read_key_file()
        return self._key

    def _read_key_file(self):
        with open(self._keyfile, 'rb') as data:
            key = data.read()
        return key

    def _create_key_file(self):
        with open(self._keyfile, 'w+') as data:
            crypto = SNCrypto()
            data.write(crypto.gen_key())
            data.close()

    def read_configuration(self):
        self.get_key()
        if not os.path.isfile(self.filename):
            # Just use default values
            return
        with open(self.filename, 'rb') as data:
            self.config = json.load(data)
            data.close()

    def save_configuration(self):
        self.get_key()
        with open(self._keyfile, 'wb') as data:
            data.write(self._key)
            data.close()
        with open(self.filename, 'wb') as data:
            json.dump(self.config, data)
            data.close()

    def merge_config_with_submitted_form(self, form):
        # Simple data binding routine to map config with submitted form
        map_config = {
            'incident_offense_map': {},
            'event_offense_map': {}
        }
        inc_map_prefix = 'incident_offense_map.'
        inc_key_prefix = inc_map_prefix + 'key.'
        inc_val_prefix = 'incident_offense_map.value.'
        evt_map_prefix = 'event_offense_map.'
        evt_key_prefix = evt_map_prefix + 'key.'
        evt_val_prefix = 'event_offense_map.value.'
        crypto = SNCrypto()
        self.get_key()
        for key, value in form.iteritems():
            if str(key).startswith(inc_key_prefix) \
                    and len(str(form[key]).strip()) > 0:
                off_val = form[inc_val_prefix + key[len(inc_key_prefix):]]
                map_config['incident_offense_map'][value] = off_val
            elif str(key).startswith(evt_key_prefix) \
                    and len(str(form[key]).strip()) > 0:
                off_val = form[evt_val_prefix + key[len(evt_key_prefix):]]
                map_config['event_offense_map'][value] = off_val
            elif key == 'password':
                if len(str(form[key]).strip()):
                    if not len(self.config.get('password')):
                        self.config['password'] = crypto.encrypt(form[key], self._key).strip()
                    elif self.config.get('password') != form[key]:
                        self.config['password'] = crypto.encrypt(form[key], self._key).strip()
                else:
                    continue
            elif key == 'proxy_password':
                if len(str(form[key]).strip()):
                    if not len(self.config.get('proxy_password')):
                        self.config['proxy_password'] = crypto.encrypt(form[key], self._key).strip()
                    elif self.config.get('proxy_password') != form[key]:
                        self.config['proxy_password'] = crypto.encrypt(form[key], self._key).strip()
                else:
                    continue
            else:
                self.config[key] = form[key]

        if 'auto_create_incidents' in form:
            self.config['auto_create_incidents'] = True
        else:
            self.config['auto_create_incidents'] = False
        if 'auto_create_events' in form:
            self.config['auto_create_events'] = True
        else:
            self.config['auto_create_events'] = False
        if 'accept_all_certs' in form:
            self.config['accept_all_certs'] = True
        else:
            self.config['accept_all_certs'] = False
        if 'show_event_button' in form:
            self.config['show_event_button'] = True
        else:
            self.config['show_event_button'] = False
        if 'show_incident_button' in form:
            self.config['show_incident_button'] = True
        else:
            self.config['show_incident_button'] = False
        self.config['incident_offense_map'] = copy.deepcopy(map_config['incident_offense_map'])
        self.config['event_offense_map'] = copy.deepcopy(map_config['event_offense_map'])
