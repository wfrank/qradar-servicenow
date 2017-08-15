__author__ = 'ServiceNow Inc.'

import copy
from app.qpylib import qpylib


class QRadar(object):
    def __init__(self, client):
        self.client = client
        self.offense_type_map = {
            '0': 'Source IP',
            '1': 'Destination IP',
            '2': 'Event Name',
            '3': 'Username',
            '4': 'Source MAC Address',
            '5': 'Destination MAC Address',
            '6': 'Log Source',
            '7': 'Hostname',
            '8': 'Source Port',
            '9': 'Destination Port',
            '10': 'Source IPv6',
            '11': 'Destination IPv6',
            '12': 'Source ASN',
            '13': 'Destination ASN',
            '14': 'Rule',
            '15': 'App Id',
            '18': 'Scheduled Search'
        }

    def get_offense_graph(self, offense_id):
        offenses = self.get_offense_graphs("id = " + offense_id)
        if offenses is None or len(offenses) == 0:
            return None
        return offenses[0]

    def get_offense_graphs(self, offense_filter):
        offenses = self.client.get_offenses(offense_filter)
        source_cache = {}
        dest_cache = {}
        for offense in offenses:
            offense['source_addresses'] = []
            offense['local_destination_addresses'] = []
            if 'source_address_ids' in offense:
                for element in offense['source_address_ids']:
                    ip_obj = None
                    if element in source_cache:
                        ip_obj = copy.deepcopy(source_cache[element])
                    else:
                        ip_obj = self.client.get_source_ip(element)
                        source_cache[element] = copy.deepcopy(ip_obj)
                    offense['source_addresses'].append(ip_obj)
            if 'local_destination_address_ids' in offense:
                for element in offense['local_destination_address_ids']:
                    ip_obj = None
                    if element in dest_cache:
                        ip_obj = copy.deepcopy(dest_cache[element])
                    else:
                        ip_obj = self.client.get_local_dest_ip(element)
                        dest_cache[element] = copy.deepcopy(ip_obj)
                    offense['local_destination_addresses'].append(ip_obj)
            if 'offense_type' in offense and str(offense['offense_type']) in self.offense_type_map:
                offense['offense_type_name'] = self.offense_type_map[str(offense['offense_type'])]
        return offenses

    def post_offense_note(self, offense_id, note):
        return self.client.post_note_to_offense(offense_id, note)

    def get_max_offense_id(self, starting_from=0):
        res = self.client.get_offenses("id >= " + str(starting_from))
        last_id = 0
        if res is None or len(res) < 1:
            return last_id
        for off in res:
            id = int(off.get('id'))
            last_id = id if id > last_id else last_id
        return last_id


class QRadarDataClient(object):
    def __init__(self, token=None, csrf=None):
        self.headers = {}
        if token is not None:
            self.headers['SEC'] = token
        if csrf is not None:
            self.headers['QRadarCSRF'] = csrf

    def get_offense(self, offense_id):
        url = '/api/siem/offenses/{0}'.format(offense_id)
        return self._do_get(url)

    def get_offenses(self, offense_filter=None):
        url = '/api/siem/offenses'
        if offense_filter is None:
            return self._do_get(url)
        else:
            parms = {'filter': offense_filter}
            return self._do_get(url, parms)

    def get_local_dest_ip(self, ip_id):
        url = '/api/siem/local_destination_addresses/{0}'.format(ip_id)
        return self._do_get(url)

    def get_source_ip(self, ip_id):
        url = '/api/siem/source_addresses/{0}'.format(ip_id)
        return self._do_get(url)

    def post_note_to_offense(self, offense_id, note):
        url = '/api/siem/offenses/{0}/notes'.format(offense_id)
        parms = {
            'note_text': note
        }
        return self._do_post(url, parms)

    def _do_get(self, resource, params=None):
        response = qpylib.REST('GET', resource, headers=self.headers, params=params)
        if response.status_code != 200:
            qpylib.log('Encountered unsuccessful response code: {0}'
                       .format(response.status_code))
            return None
        return response.json()

    def _do_post(self, resource, params):
        response = qpylib.REST('POST', resource, headers=self.headers, params=params)
        if response.status_code != 201:
            qpylib.log('Encountered unsuccessful response code: {0}'
                       .format(response.status_code))
            return None
        return response.json()
