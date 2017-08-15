#!/usr/bin/python

# (C) Copyright IBM Corp. 2015, 2016
# The source code for this program is not published or
# otherwise divested of its trade secrets, irrespective of
# what has been deposited with the US Copyright Office.

from abstract_qpylib import AbstractQpylib
import json
import os
import os.path
import sys
import getpass
import logging

dev_auth_file = ".qradar_appfw.auth"
dev_console_file = ".qradar_appfw.console"
yes = ("y", "yes")
no = ("no", "n")

api_auth_user = 0
api_auth_password = 0
consoleIP = 0
handler_added = 0

manifest_location = 'manifest.json'

class SdkQpylib(AbstractQpylib):

    def get_manifest_location(self):
        global manifest_location
        return manifest_location

    def get_app_id(self):
        return "DEV_APP"

    def get_app_name(self):
        return "SDK_APP"

    def get_console_address(self):
        global consoleIP
        global dev_console_file
        home = os.path.expanduser("~")
        console_file_path = os.path.join(home, dev_console_file)
        if os.path.isfile(console_file_path):
            print("Loading console details from file: " + str(console_file_path))
            sys.stdout.flush()
            with open(console_file_path) as consolefile:
                console_json = json.load(consolefile)
            consoleIP = console_json["console"]
        else:
            if consoleIP == 0:
                console_data = {}
                print("What is the IP of QRadar console"),
                print("required to make this API call:")
                sys.stdout.flush()
                consoleIP = raw_input()
                console_data['console'] = consoleIP
                print("Do you want to store the console IP at:" + console_file_path)
                print("[y/n]:")
                sys.stdout.flush()
                do_store = raw_input()
                if do_store in yes:
                    with open(console_file_path, 'w+') as console_file:
                        json.dump(console_data, console_file)
        return consoleIP

    def get_api_auth(self):
        auth = None
        global dev_auth_file
        global api_auth_user
        global api_auth_password
        home = os.path.expanduser("~")
        auth_file_path = os.path.join(home, dev_auth_file)
        if os.path.isfile(auth_file_path):
            print("Loading user details from file: " + str(auth_file_path))
            sys.stdout.flush()
            with open(auth_file_path) as authfile:
                auth_json = json.load(authfile)
                auth = (auth_json["user"], auth_json["password"])
        else:
            auth_data = {}
            consoleAddress = self.get_console_address()
            print("QRadar credentials for " + consoleAddress + " are required to make this API call:")
            if api_auth_user == 0:
                print( "User:" )
                sys.stdout.flush()
                api_auth_user = raw_input()
            if api_auth_password == 0:
                api_auth_password = getpass.getpass("Password:")
                auth_data['user'] = api_auth_user
                auth_data['password'] = api_auth_password
                print("Store credentials credentials at:" + auth_file_path)
                print("WARNING: credentials will be stored in clear.")
                print("[y/n]:")
                sys.stdout.flush()
                do_store = raw_input()
                if do_store in yes:
                    with open(auth_file_path, 'w+') as auth_file:
                        json.dump(auth_data, auth_file)
            auth = (api_auth_user, api_auth_password)
        print( "Using Auth: " + str(auth) )
        return auth

    def REST(self, RESTtype, requestURL, headers=None, data=None, params=None, json_inst=None, version=None):
        if headers is None:
            headers={}
        if version is not None:
            headers['Version'] = version
        auth = self.get_api_auth()
        fullURL = "https://" + str(self.get_console_address()) + "/" + str(requestURL)
        rest_func = self.chooseREST(RESTtype)
        return rest_func(URL=fullURL, headers=headers, data=data, auth=auth, params=params, json_inst=json_inst)

    def add_log_handler(self, loc_logger):
        global handler_added
        if 0 == handler_added:
            loc_logger.setLevel(self.map_log_level('debug'))
            handler = logging.StreamHandler()
            loc_logger.addHandler(handler)
            handler_added=1

    def root_path(self):
        return os.getenv('QRADAR_APPFW_WORKSPACE', '~')

    def get_app_base_url(self):
        return "http://localhost:5000"
