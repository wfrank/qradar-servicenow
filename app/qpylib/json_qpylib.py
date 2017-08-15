#!/usr/bin/python

# (C) Copyright IBM Corp. 2015, 2016
# The source code for this program is not published or
# otherwise divested of its trade secrets, irrespective of
# what has been deposited with the US Copyright Office.

import json

# A dictionary of jsonld context types mapped to the type name
jsonld_types = {}

def register_jsonld_type(jsonld_type, context):
    global jsonld_types
    jsonld_types[str(jsonld_type)] = context

def get_jsonld_type(jsonld_type):
    global jsonld_types
    if jsonld_type in jsonld_types.keys():
        return jsonld_types[str(jsonld_type)]
    else:
        raise ValueError('json ld key has not been registered')

def render_json_ld_type(jld_type, data, jld_id = None):
    jld_context = get_jsonld_type(jld_type)
    json_dict = {}
    for json_key in data:
        json_dict[json_key] = data[json_key]

    json_dict['@context']=jld_context['@context']
    json_dict['@type']=jld_type
    if None != jld_id:
        json_dict['@type']=jld_type

    return json.dumps(json_dict, sort_keys=True)

def json_ld(jld_context, jld_id, jld_type, name, description, data):
    return json.dumps({'@context': jld_context, '@id': jld_id, '@type': jld_type, 'name': name,
                       'description': description, 'data': data}, sort_keys=True)

def json_html(html):
    return json.dumps({'html': html})
