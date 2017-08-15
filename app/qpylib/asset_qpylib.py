#!/usr/bin/python

# (C) Copyright IBM Corp. 2015, 2016
# The source code for this program is not published or
# otherwise divested of its trade secrets, irrespective of
# what has been deposited with the US Copyright Office.

import qpylib
import json_qpylib

# Context location yet to be finalised.
JSON_LD_CONTEXT = 'http://qradar/context/location'

# The api method to GET an individual asset is not yet supported.
def get_asset_url(asset_id):
    return 'api/asset_model/assets/' + asset_id

def get_asset_url_full(asset_id):
    return 'https://' + qpylib.get_console_address() + '/' + get_asset_url(asset_id)

def get_asset_json(asset_id):
    # Actual implementation commented out for now - see get_asset_url above
    #response = qpylib.REST('get', get_asset_url(asset_id))
    #if response.status_code != 200:
    #    raise ValueError('Could not retrieve asset')
    #return response.json()
    asset_json = {}
    asset_json['id'] = asset_id
    return asset_json

def get_asset_json_ld(asset_id):
    asset_json = get_asset_json(asset_id)
    return json_qpylib.json_ld(JSON_LD_CONTEXT,
                               get_asset_url_full(asset_id),
                               'asset',
                               'Asset details',
                               'Asset details for id ' + asset_id,
                               asset_json)

def get_asset_json_html(asset_id, generate_html = None):
    asset_json = get_asset_json(asset_id)
    if generate_html is None:
        asset_html = get_asset_html_example(asset_json)
    else:
        asset_html = generate_html(asset_json)
    return json_qpylib.json_html(asset_html)

def get_asset_html_example(asset_json):
    return ('<table><tbody>' +
            '<tr><td>Asset ID</td><td>' + str(asset_json['id']) + '</td></tr>' +
            '</tbody></table>')
