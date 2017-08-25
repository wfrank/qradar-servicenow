import json
import os
import copy
from app.models.crypto import CryptoUtils

from app.qpylib import qpylib


class ServiceNowConfiguration(object):
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
            'offense_map': {
                'short_description': 'QRadar-{{ offense.id }} - {{ offense.description }}',
                'description': 'QRadar-{{ offense.id }} - {{ offense.description }}',
                'cmdb_ci': '{{ offense.local_destination_addresses[0].local_destination_ip }}',
                'severity': '{{ 3 - (offense.severity /10 * 2)|round|int }}',
                'source_ip': '{{ offense.source_addresses[0].source_ip }}',
                'dest_ip': '{{ offense.local_destination_addresses[0].local_destination_ip }}'
            },
            'group_map': {},
            'auto_create_incidents': False,
            'auto_close_offenses': True,
            'auto_sync_frequency': 60,
            'offense_filter': '',
            'proxy_url': '',
            'proxy_username': '',
            'proxy_password': '',
            'accept_all_certs': False,
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
            crypto = CryptoUtils()
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
            'offense_map': {},
            'group_map': {}
        }
        ofs_map_prefix = 'offense_map.'
        ofs_key_prefix = ofs_map_prefix + 'key.'
        ofs_val_prefix = 'offense_map.value.'
        grp_map_prefix = 'group_map.'
        grp_key_prefix = grp_map_prefix + 'key.'
        grp_val_prefix = 'group_map.value.'
        crypto = CryptoUtils()
        self.get_key()
        for key, value in form.iteritems():
            if str(key).startswith(ofs_key_prefix) \
                    and len(str(form[key]).strip()) > 0:
                off_val = form[ofs_val_prefix + key[len(ofs_key_prefix):]]
                map_config['offense_map'][value] = off_val
            elif str(key).startswith(grp_key_prefix) \
                    and len(str(form[key]).strip()) > 0:
                grp_val = form[grp_val_prefix + key[len(grp_key_prefix):]]
                map_config['group_map'][value] = grp_val
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
            self.config['auto_send_offenses'] = False
        if 'auto_close_offenses' in form:
            self.config['auto_close_offenses'] = True
        else:
            self.config['auto_close_offenses'] = False
        if 'accept_all_certs' in form:
            self.config['accept_all_certs'] = True
        else:
            self.config['accept_all_certs'] = False
        self.config['offense_map'] = copy.deepcopy(map_config['offense_map'])
        self.config['group_map'] = copy.deepcopy(map_config['group_map'])
