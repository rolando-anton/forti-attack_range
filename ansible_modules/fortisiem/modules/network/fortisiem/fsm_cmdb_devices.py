#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = '''
---
module: fsm_cmdb_devices
version_added: "2.8"
author: Luke Weighall (@lweighall)
short_description: Get a list of devices from the FortiSIEM CMDB
description:
  - Gets a short description of each device in the FortiSIEM CMDB and returns the data

options:
  host:
    description:
      - The FortiSIEM's FQDN or IP Address.
    required: true

  username:
    description:
      - The username used to authenticate with the FortiManager.
      - organization/username format. The Organization is important, and will only return data from specified Org.
    required: false

  password:
    description:
      - The password associated with the username account.
    required: false

  ignore_ssl_errors:
    description:
      - When Enabled this will instruct the HTTP Libraries to ignore any ssl validation errors.
    required: false
    default: "enable"
    choices: ["enable", "disable"]

  export_json_to_screen:
    description:
      - When enabled this will print the JSON results to screen.
    required: false
    default: "enable"
    choices: ["enable", "disable"]

  export_json_to_file_path:
    description:
      - When populated, an attempt to write JSON dictionary to file is made.
      - An error will be thrown if this fails.
    required: false
    default: None

  export_xml_to_file_path:
    description:
      - When populated, an attempt to write XML to file is made.
      - An error will be thrown if this fails.
    required: false
    default: None

  mode:
    description:
      - Handles how the query is formatted.
    required: false
    default: "short_all"
    choices: ["short_all", "ip_range", "detailed_single"]

  ip_range:
    description:
      - Specifies the IP Range of devices to search for and return.
      - Ignored unless "ip_range" is set for mode
    required: false

  ip:
    description:
      - Specifies the single IP address of a device to get detailed information from.
      - Ignored unless "detailed_single" is set for mode
    required: false

'''

EXAMPLES = '''
- name: GET SIMPLE DEVICE LIST FROM CMDB
  fsm_cmdb_devices:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"
    mode: "short_all"

- name: GET SIMPLE DEVICE LIST FROM CMDB IP RANGE
  fsm_cmdb_devices:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"
    mode: "ip_range"
    ip_range: "10.0.0.100-10.0.0.120"

- name: GET DETAILED INFO ON ONE DEVICE
  fsm_cmdb_devices:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"
    mode: "detailed_single"
    ip: "10.0.0.5"


'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortisiem.common import FSMEndpoints
from ansible.module_utils.network.fortisiem.common import FSMBaseException
from ansible.module_utils.network.fortisiem.common import DEFAULT_EXIT_MSG
from ansible.module_utils.network.fortisiem.fortisiem import FortiSIEMHandler


def main():
    argument_spec = dict(
        host=dict(required=True, type="str"),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        ignore_ssl_errors=dict(required=False, type="str", choices=["enable", "disable"], default="enable"),
        export_json_to_screen=dict(required=False, type="str", choices=["enable", "disable"], default="enable"),
        export_json_to_file_path=dict(required=False, type="str"),
        export_xml_to_file_path=dict(required=False, type="str"),
        export_csv_to_file_path=dict(required=False, type="str"),

        mode=dict(required=False, type="str",
                  choices=["short_all", "ip_range", "detailed_single"], default="short_all"),
        ip_range=dict(required=False, type="str"),
        ip=dict(required=False, type="str")
    )

    required_if = [
        ['mode', 'ip_range', ['ip_range']],
        ['mode', 'detailed_single', ['ip']],
    ]

    module = AnsibleModule(argument_spec, supports_check_mode=False, required_if=required_if)

    paramgram = {
        "host": module.params["host"],
        "username": module.params["username"],
        "password": module.params["password"],
        "export_json_to_screen": module.params["export_json_to_screen"],
        "export_json_to_file_path": module.params["export_json_to_file_path"],
        "export_xml_to_file_path": module.params["export_xml_to_file_path"],
        "export_csv_to_file_path": module.params["export_csv_to_file_path"],
        "ignore_ssl_errors": module.params["ignore_ssl_errors"],

        "mode": module.params["mode"],
        "uri": None
    }

    # DETERMINE THE MODE AND ADD THE CORRECT DATA TO THE PARAMGRAM
    if paramgram["mode"] == "short_all":
        paramgram["uri"] = FSMEndpoints.GET_CMDB_SHORT
    elif paramgram["mode"] == "ip_range":
        paramgram["uri"] = FSMEndpoints.GET_CMDB_IPRANGE + module.params["ip_range"]
    elif paramgram["mode"] == "detailed_single":
        paramgram["uri"] = FSMEndpoints.GET_CMDB_DETAILED_SINGLE + module.params["ip"] + "&loadDepend=true"

    if paramgram["uri"] is None:
        raise FSMBaseException("Base URI couldn't be constructed. Check options.")

    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    fsm = None
    results = DEFAULT_EXIT_MSG
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))
    # EXECUTE THE MODULE OPERATION
    try:
        results = fsm.handle_simple_request()
    except BaseException as err:
        raise FSMBaseException(err)
    # EXIT USING GOVERN_RESPONSE()
    fsm.govern_response(module=module, results=results, changed=False,
                        ansible_facts=fsm.construct_ansible_facts(results["json_results"],
                                                                  module.params,
                                                                  paramgram))

    return module.exit_json(msg=results)


if __name__ == "__main__":
    main()
