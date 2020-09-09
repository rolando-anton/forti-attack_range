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
module: fsm_device_monitors
version_added: "2.8"
author: Luke Weighall (@lweighall)
short_description: Get a list of monitors for specified devices.
description:
  - Gets a short description of each devices monitors status in FortiSIEM.
  - Results are returned via dictionary json with the key "summary"

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
      - Handles how the query is formatted upon return.
      - When in update mode, update_xml_file is required.
    required: false
    default: "short_all"
    choices: ["short_all", "ip_range", "detailed_single", "update"]

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

  update_xml_file:
    description:
      - Specifies the XML file path that contains the pre-formatted XML to update the monitor with.
    required: false

'''

EXAMPLES = '''
- name: GET SIMPLE MONITOR LIST FROM CMDB
  fsm_device_monitors:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    mode: "short_all"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/monitors_out1.json"
    export_xml_to_file_path: "/root/monitors_out1.xml"

- name: GET SIMPLE MONITOR LIST FROM CMDB IP RANGE
  fsm_device_monitors:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    mode: "ip_range"
    ip_range: "10.0.0.5-10.0.0.15"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/monitors_out2.json"
    export_xml_to_file_path: "/root/monitors_out2.xml"

- name: GET DETAILED MONITOR INFO ON ONE DEVICE
  fsm_device_monitors:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    mode: "detailed_single"
    ip: "10.0.0.5"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/monitors_out3.json"
    export_xml_to_file_path: "/root/monitors_out3.xml"
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
from ansible.module_utils.network.fortisiem.common import FSMCommon
from ansible.module_utils.network.fortisiem.fortisiem import FortiSIEMHandler
import re


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
                  choices=["short_all", "ip_range", "detailed_single", "update"], default="short_all"),
        ip_range=dict(required=False, type="str"),
        ip=dict(required=False, type="str"),
        update_xml_file=dict(required=False, type="str")
    )

    required_if = [
        ['mode', 'ip_range', ['ip_range']],
        ['mode', 'detailed_single', ['ip']],
        ['mode', 'update', ['update_xml_file']],
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
        "ip_range": module.params["ip_range"],
        "ip": module.params["ip"],
        "update_xml_file": module.params["update_xml_file"],
        "mode": module.params["mode"],
        "uri": None
    }

    # DETERMINE THE MODE AND ADD THE CORRECT DATA TO THE PARAMGRAM
    if paramgram["mode"] in ["short_all", "ip_range", "detailed_single"]:
        paramgram["uri"] = FSMEndpoints.GET_MONITORED_DEVICES
    elif paramgram["mode"] == "update":
        paramgram["uri"] = FSMEndpoints.UPDATE_DEVICE_MONITORING

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

    # RUN IF MODE = SHORT ALL
    if paramgram["mode"] == "short_all":
        try:
            results = fsm.handle_simple_request()
        except BaseException as err:
            raise FSMBaseException(err)
        # ADD A SUMMARY TO THE RESULTS
        try:
            results = fsm._tools.get_monitors_summary_for_short_all(results)
        except BaseException as err:
            raise FSMBaseException(err)

    # RUN IF MODE = IP RANGE
    if paramgram["mode"] == "ip_range":
        try:
            results = fsm.handle_simple_request()
        except BaseException as err:
            raise FSMBaseException(err)
        # FOR EACH IP ADDRESS IN RANGE, RUN THE METHOD get_monitors_info_for_specific_ip

        try:
            ipr = str(paramgram["ip_range"]).split("-")
            ipr_list = FSMCommon.get_ip_list_from_range(ipr[0], ipr[1])
        except BaseException as err:
            raise FSMBaseException(err)
        try:
            results_append_list = []
            for ip in ipr_list:
                append = fsm._tools.get_monitors_info_for_specific_ip(results, str(ip))
                if len(append) > 0:
                    results_append_list.append(append)
            results["json_results"]["summary"] = results_append_list
            # REMOVE THE FULL QUERY TO CLEAN UP THE RESULTS
            del results["json_results"]["monitoredDevices"]
        except BaseException as err:
            raise FSMBaseException(err)

    # RUN IF MODE = SINGLE IP ADDRESS
    if paramgram["mode"] == "detailed_single":
        try:
            results = fsm.handle_simple_request()
        except BaseException as err:
            raise FSMBaseException(err)
        results_append_list = []
        append = fsm._tools.get_monitors_info_for_specific_ip(results, paramgram["ip"])
        if len(append) > 0:
            results_append_list.append(append)
        results["json_results"]["summary"] = results_append_list
        # REMOVE THE FULL QUERY TO CLEAN UP THE RESULTS
        del results["json_results"]["monitoredDevices"]
        if isinstance(results["json_results"]["summary"], dict):
            # CONVERT SUMMARY DICT INTO XML
            results["xml_results"] = fsm._tools.dict2xml(results["json_results"]["summary"])
        elif isinstance(results["json_results"]["summary"], list):
            temp_xml_dict = {"results": results["xml_results"]}
            results["xml_results"] = fsm._tools.dict2xml(temp_xml_dict)

    # RUN IF MODE = UPDATE
    if paramgram["mode"] == "update":
        try:
            paramgram["input_xml"] = fsm.get_file_contents(paramgram["update_xml_file"])
            paramgram["input_xml"] = re.sub(r'\n', '', paramgram["input_xml"])
        except BaseException as err:
            raise FSMBaseException(msg="Couldn't find or load update_xml_file path. Double check. Error: " + str(err))
        # REFRESH PARAMGRAM
        module.paramgram = paramgram
        try:
            results = fsm.handle_simple_payload_request(str(paramgram["input_xml"]))
        except BaseException as err:
            raise FSMBaseException(err)
        # CONVERT SUMMARY DICT INTO XML
        results["xml_results"] = fsm._tools.dict2xml(results["json_results"])

    # EXIT USING GOVERN_RESPONSE()
    fsm.govern_response(module=module, results=results, changed=False, good_codes=[200, 204],
                        ansible_facts=fsm.construct_ansible_facts(results["json_results"],
                                                                  module.params,
                                                                  paramgram))
    # elif paramgram["mode"] == "update":

    return module.exit_json(msg=results)


if __name__ == "__main__":
    main()
