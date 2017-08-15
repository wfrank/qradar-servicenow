#!/usr/bin/python

# (C) Copyright IBM Corp. 2015, 2016
# The source code for this program is not published or
# otherwise divested of its trade secrets, irrespective of
# what has been deposited with the US Copyright Office.

from abstract_qpylib import AbstractQpylib
from logging.handlers import RotatingFileHandler, SysLogHandler
from logging import Formatter
from flask import request

manifest_location = 'app/manifest.json'
logfile_location = '/store/log/app.log'


class LiveQpylib(AbstractQpylib):

    def get_manifest_location(self):
        global manifest_location
        return manifest_location

    def get_console_address(self):
        manifest = self.get_manifest_json()
        console_ip = ''
        if 'console_ip' not in manifest:
            self.log('console not defined in manifest - default to localhost',
                level='error')
            console_ip = '127.0.0.1'
        else:
            console_ip = manifest['console_ip']
        return console_ip

    def acquire_SEC_token(self):
        return request.cookies.get('SEC')

    def acquire_QRadarCSRF_token(self):
        return request.cookies.get('QRadarCSRF')

    def get_tokens(self, headers, version=None):
        if headers is None:
            headers = {}
        if 'SEC' not in headers:
            headers['SEC'] = self.acquire_SEC_token()
        if 'QRadarCSRF' not in headers:
            headers['QRadarCSRF'] = self.acquire_QRadarCSRF_token()
        if version is not None:
            headers['Version'] = version
        return headers

    def get_manifest_log_level(self):
        log_level = 'info'
        manifest = self.get_manifest_json()
        if 'log_level' in manifest.keys():
            log_level = manifest["log_level"]
        return log_level

    def add_log_handler(self, loc_logger):
        global logfile_location
        loc_logger.setLevel(self.map_log_level(self.get_manifest_log_level()))
        handler = RotatingFileHandler(logfile_location, maxBytes=2*1024*1024, backupCount=5)
        handler.setFormatter(Formatter('%(asctime)s [%(module)s.%(funcName)s] [%(threadName)s] [%(levelname)s] - %(message)s'))
        loc_logger.addHandler(handler)
        syslogHandler = SysLogHandler(address=(self.get_console_address(), 514))
        syslogHandler.setFormatter(Formatter('%(asctime)s %(module)s.%(funcName)s: %(message)s'))
        loc_logger.addHandler(syslogHandler)
        return

    def REST(self, RESTtype, requestURL, headers=None, data=None,
             params=None, json_inst=None, version=None):
        headers = self.get_tokens(headers, version)
        fullURL = "https://" + self.get_console_address() + "/" + requestURL
        self.log("REST " + fullURL +
                  "RESTtype " + RESTtype +
                  "headers " + str(headers) +
                  "data " + str(data) +
                  "params " + str(params) +
                  "json " + str(json_inst) +
                  "version " + str(version), 'debug')
        return self.chooseREST(RESTtype)(URL=fullURL, headers=headers,
                                         data=data, params=params, json_inst=json_inst)

    def get_app_name(self):
        manifest = self.get_manifest_json()
        app_name = 'None'
        if 'name' in manifest.keys():
            app_name = str(manifest["name"])
        return app_name

    def get_app_id(self):
        manifest = self.get_manifest_json()
        app_id = '0'
        if 'app_id' in manifest.keys():
            app_id = str(manifest["app_id"])
        return app_id

    def get_app_base_url(self):
        """
        Get the full url through QRadar, that will proxy any request to the
        appropriate Application plugin servlet
        """
        self.log("getAppBaseUrl>>>", 'debug')
        proxy_path = ''

        # read /app/manifest.json
        # get 'console_ip' and 'app_id' fields
        # concat into url format:
        # https://{console_ip}/console/plugins/{<}app_id}/app_proxy
        console_ip = ''
        url_suffix = ''
        manifest = self.get_manifest_json()
        if 'console_ip' in manifest.keys():
            console_ip = str(manifest["console_ip"])
        if 'app_id' in manifest.keys():
            app_id = str(manifest["app_id"])
            url_suffix = "/console/plugins/" + app_id + "/app_proxy"
        proxy_path = "https://" + console_ip + url_suffix

        self.log("proxy_path==>" + proxy_path, 'debug')
        self.log("<<<getAppBaseUrl", 'debug')
        return proxy_path

    def root_path(self):
        return "/"
