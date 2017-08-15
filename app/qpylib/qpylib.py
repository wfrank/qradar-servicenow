#!/usr/bin/python

# (C) Copyright IBM Corp. 2015, 2016
# The source code for this program is not published or
# otherwise divested of its trade secrets, irrespective of
# what has been deposited with the US Copyright Office.

import os
from sdk_qpylib import SdkQpylib
from live_qpylib import LiveQpylib

# ===== SDK specifics =====

def is_sdk():
    sdk_env = os.getenv('QRADAR_APPFW_SDK', 'no').lower() == 'true'
    return sdk_env

def strategy():
    strategy_impl = LiveQpylib()
    if is_sdk():
        strategy_impl = SdkQpylib()
    return strategy_impl

# ===== User Utils qpylib =====

def log(message, level='info'):
    strategy().log(message, level)

def create_log():
    strategy().create_log()

def set_log_level(log_level='info'):
    strategy().set_log_level(log_level)

def get_store_path(relative_path=""):
    return strategy().get_store_path(relative_path)

def get_root_path(relative_path=""):
    return strategy().get_root_path(relative_path)

def REST(RESTtype, requestURL, headers=None, data=None, params=None,
         json=None, version=None):
    return strategy().REST(RESTtype, requestURL, headers, data=data,
                           params=params, json_inst=json,
                           version=version)

def get_app_base_url():
    return strategy().get_app_base_url()

def q_url_for(endpoint, **values):
    return strategy().q_url_for(endpoint, **values)

def to_json_dict(python_obj):
    return strategy().to_json_dict(python_obj)

def get_console_address():
    return strategy().get_console_address()

def get_app_id():
    return strategy().get_app_id()

def get_app_name():
    return strategy().get_app_name()

def register_jsonld_type(context):
    return strategy().register_jsonld_type(context)

# ==== Rendering Utils ====

def get_offense_rendering(offense_id, render_type):
    return strategy().get_offense_rendering(offense_id, render_type)

def get_asset_rendering(asset_id, render_type):
    return strategy().get_asset_rendering(asset_id, render_type)

def render_json_ld_type(jld_type, data, jld_id = None):
    return strategy().render_json_ld_type(jld_type, data, jld_id)

def register_jsonld_endpoints():
    return strategy().register_jsonld_endpoints()
