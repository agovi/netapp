#!/usr/bin/python

# (c) 2017-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

'''
na_ontap_lun
'''

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_lun

short_description: NetApp ONTAP manage LUNs
extends_documentation_fragment:
    - netapp.ontap.netapp.na_ontap
version_added: 2.6.0
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Create, destroy, resize LUNs on NetApp ONTAP.

options:

  state:
    description:
    - Whether the specified LUN should exist or not.
    choices: ['present', 'absent']
    type: str
    default: present

  name:
    description:
    - The name of the LUN to manage.
    required: true
    type: str

  from_name:
    description:
    - The name of the LUN to be renamed.
    type: str
    version_added: 20.12.0

  flexvol_name:
    description:
    - The name of the FlexVol the LUN should exist on.
    - Required if san_application_template is not present.
    - Not allowed if san_application_template is present.
    type: str

  size:
    description:
    - The size of the LUN in C(size_unit).
    - Required when C(state=present).
    type: int

  size_unit:
    description:
    - The unit used to interpret the size parameter.
    choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    default: 'gb'
    type: str

  force_resize:
    description:
      Forcibly reduce the size. This is required for reducing the size of the LUN to avoid accidentally
      reducing the LUN size.
    type: bool
    default: false

  force_remove:
    description:
    - If "true", override checks that prevent a LUN from being destroyed if it is online and mapped.
    - If "false", destroying an online and mapped LUN will fail.
    type: bool
    default: false

  force_remove_fenced:
    description:
    - If "true", override checks that prevent a LUN from being destroyed while it is fenced.
    - If "false", attempting to destroy a fenced LUN will fail.
    - The default if not specified is "false". This field is available in Data ONTAP 8.2 and later.
    type: bool
    default: false

  vserver:
    required: true
    description:
    - The name of the vserver to use.
    type: str

  os_type:
    description:
    - The os type for the LUN.
    type: str
    aliases: ['ostype']

  qos_policy_group:
    description:
    - The QoS policy group to be set on the LUN.
    type: str
    version_added: 20.12.0

  space_reserve:
    description:
    - This can be set to "false" which will create a LUN without any space being reserved.
    type: bool
    default: True

  space_allocation:
    description:
    - This enables support for the SCSI Thin Provisioning features.  If the Host and file system do
      not support this do not enable it.
    type: bool
    default: False
    version_added: 2.7.0

  use_exact_size:
    description:
    - This can be set to "False" which will round the LUN >= 450g.
    type: bool
    default: True
    version_added: 20.11.0

  san_application_template:
    description:
      - additional options when using the application/applications REST API to create LUNs.
      - the module is using ZAPI by default, and switches to REST if any suboption is present.
      - create one or more LUNs (and the associated volume as needed).
      - only creation or deletion of a SAN application is supported.  Changes are ignored.
      - operations at the LUN level are supported, they require to know the LUN short name.
      - this requires ONTAP 9.6 or higher.
    type: dict
    version_added: 20.12.0
    suboptions:
      name:
        description: name of the SAN application.
        type: str
        required: True
      igroup_name:
        description: name of the initiator group through which the contents of this application will be accessed.
        type: str
      lun_count:
        description: number of LUNs in the application component (1 to 32).
        type: int
      protection_type:
        description:
          - The snasphot policy for the volume supporting the LUNs.
        type: dict
        suboptions:
          local_policy:
            description:
              - The snapshot copy policy for the volume.
            type: str
      storage_service:
        description:
          - The performance service level (PSL) for this volume
        type: str
        choices: ['value', 'performance', 'extreme']
      tiering:
        description:
          - Cloud tiering policy.
        type: dict
        suboptions:
          control:
            description: Storage tiering placement rules for the container.
            choices: ['required', 'best_effort', 'disallowed']
            type: str
          policy:
            description:
              - Cloud tiering policy.
            choices: ['all', 'auto', 'none', 'snapshot-only']
            type: str
          object_stores:
            description: list of object store names for tiering.
            type: list
            elements: str
      use_san_application:
        description:
          - Whether to use the application/applications REST/API to create LUNs.
          - This will default to true if any other suboption is present.
        type: bool
        default: true

'''

EXAMPLES = """
- name: Create LUN
  na_ontap_lun:
    state: present
    name: ansibleLUN
    flexvol_name: ansibleVolume
    vserver: ansibleVServer
    size: 5
    size_unit: mb
    os_type: linux
    space_reserve: True
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Resize LUN
  na_ontap_lun:
    state: present
    name: ansibleLUN
    force_resize: True
    flexvol_name: ansibleVolume
    vserver: ansibleVServer
    size: 5
    size_unit: gb
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Create LUNs using SAN application
  tags: create
  na_ontap_lun:
    state: present
    name: ansibleLUN
    size: 15
    size_unit: mb
    os_type: linux
    space_reserve: false
    san_application_template:
      name: san-ansibleLUN
      igroup_name: testme_igroup
      lun_count: 3
      protection_type:
      local_policy: default
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"
"""

RETURN = """

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible_collections.netapp.ontap.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.ontap.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.ontap.plugins.module_utils.rest_application import RestApplication

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapLUN(object):
    ''' create, modify, delete LUN '''
    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str'),
            size=dict(type='int'),
            size_unit=dict(default='gb',
                           choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb',
                                    'pb', 'eb', 'zb', 'yb'], type='str'),
            force_resize=dict(default=False, type='bool'),
            force_remove=dict(default=False, type='bool'),
            force_remove_fenced=dict(default=False, type='bool'),
            flexvol_name=dict(type='str'),
            vserver=dict(required=True, type='str'),
            os_type=dict(required=False, type='str', aliases=['ostype']),
            qos_policy_group=dict(required=False, type='str'),
            space_reserve=dict(required=False, type='bool', default=True),
            space_allocation=dict(required=False, type='bool', default=False),
            use_exact_size=dict(required=False, type='bool', default=True),
            san_application_template=dict(type='dict', options=dict(
                use_san_application=dict(type='bool', default=True),
                name=dict(required=True, type='str'),
                igroup_name=dict(type='str'),
                lun_count=dict(type='int'),
                protection_type=dict(type='dict', options=dict(
                    local_policy=dict(type='str'),
                )),
                storage_service=dict(type='str', choices=['value', 'performance', 'extreme']),
                tiering=dict(type='dict', options=dict(
                    control=dict(type='str', choices=['required', 'best_effort', 'disallowed']),
                    policy=dict(type='str', choices=['all', 'auto', 'none', 'snapshot-only']),
                    object_stores=dict(type='list', elements='str')     # create only
                )),
            ))
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        # set up state variables
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        if self.parameters.get('size') is not None:
            self.parameters['size'] *= netapp_utils.POW2_BYTE_MAP[self.parameters['size_unit']]

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

        # REST API for application/applications if needed
        self.rest_api, self.rest_app = self.setup_rest_application()

    def setup_rest_application(self):
        use_application_template = self.na_helper.safe_get(self.parameters, ['san_application_template', 'use_san_application'])
        rest_api, rest_app = None, None
        if use_application_template:
            if self.parameters.get('flexvol_name') is not None:
                self.module.fail_json(msg="'flexvol_name' option is not supported when san_application_template is present")
            rest_api = netapp_utils.OntapRestAPI(self.module)
            name = self.na_helper.safe_get(self.parameters, ['san_application_template', 'name'], allow_sparse_dict=False)
            rest_app = RestApplication(rest_api, self.parameters['vserver'], name)
        elif self.parameters.get('flexvol_name') is None:
            self.module.fail_json(msg="flexvol_name option is required when san_application_template is not present")
        return rest_api, rest_app

    def get_luns(self, lun_path=None):
        """
        Return list of LUNs matching vserver and volume names.

        :return: list of LUNs in XML format.
        :rtype: list
        """
        luns = []
        tag = None
        if lun_path is None and self.parameters.get('flexvol_name') is None:
            return luns

        query_details = netapp_utils.zapi.NaElement('lun-info')
        query_details.add_new_child('vserver', self.parameters['vserver'])
        if lun_path is not None:
            query_details.add_new_child('lun_path', lun_path)
        else:
            query_details.add_new_child('volume', self.parameters['flexvol_name'])
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)

        while True:
            lun_info = netapp_utils.zapi.NaElement('lun-get-iter')
            lun_info.add_child_elem(query)
            if tag:
                lun_info.add_new_child('tag', tag, True)

            result = self.server.invoke_successfully(lun_info, True)
            if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
                attr_list = result.get_child_by_name('attributes-list')
                luns.extend(attr_list.get_children())
            tag = result.get_child_content('next-tag')
            if tag is None:
                break
        return luns

    def get_lun_details(self, lun):
        """
        Extract LUN details, from XML to python dict

        :return: Details about the lun
        :rtype: dict
        """
        return_value = dict()
        return_value['size'] = int(lun.get_child_content('size'))
        bool_attr_map = {
            'is-space-alloc-enabled': 'space_allocation',
            'is-space-reservation-enabled': 'space_reserve'
        }
        for attr in bool_attr_map:
            value = lun.get_child_content(attr)
            if value is not None:
                return_value[bool_attr_map[attr]] = self.na_helper.get_value_for_bool(True, value)
        str_attr_map = {
            'name': 'name',
            'path': 'path',
            'qos-policy-group': 'qos_policy_group',
            'multiprotocol-type': 'os_type'
        }
        for attr in str_attr_map:
            value = lun.get_child_content(attr)
            if value is not None:
                return_value[str_attr_map[attr]] = value

        # Find out if the lun is attached
        attached_to = None
        lun_id = None
        if lun.get_child_content('mapped') == 'true':
            lun_map_list = netapp_utils.zapi.NaElement.create_node_with_children(
                'lun-map-list-info', **{'path': lun.get_child_content('path')})
            result = self.server.invoke_successfully(
                lun_map_list, enable_tunneling=True)
            igroups = result.get_child_by_name('initiator-groups')
            if igroups:
                for igroup_info in igroups.get_children():
                    igroup = igroup_info.get_child_content(
                        'initiator-group-name')
                    attached_to = igroup
                    lun_id = igroup_info.get_child_content('lun-id')

        return_value.update({
            'attached_to': attached_to,
            'lun_id': lun_id
        })
        return return_value

    def find_lun(self, luns, name, lun_path=None):
        """
        Return lun record matching name or path

        :return: lun record
        :rtype: XML or None if not found
        """
        for lun in luns:
            path = lun.get_child_content('path')
            if lun_path is not None:
                if lun_path == path:
                    return lun
            else:
                if name == path:
                    return lun
                _rest, _splitter, found_name = path.rpartition('/')
                if found_name == name:
                    return lun
        return None

    def get_lun(self, name, lun_path=None):
        """
        Return details about the LUN

        :return: Details about the lun
        :rtype: dict
        """
        luns = self.get_luns(lun_path)
        lun = self.find_lun(luns, name, lun_path)
        if lun is not None:
            return self.get_lun_details(lun)
        return None

    def get_luns_from_app(self):
        app_details, error = self.rest_app.get_application_details()
        self.fail_on_error(error)
        if app_details is not None:
            app_details['paths'] = self.get_lun_paths_from_app()
        return app_details

    def get_lun_paths_from_app(self):
        """Get luns path for SAN application"""
        backing_storage, error = self.rest_app.get_application_component_backing_storage()
        self.fail_on_error(error)
        # {'luns': [{'path': '/vol/ansibleLUN/ansibleLUN_1', ...
        if backing_storage is not None:
            return [lun['path'] for lun in backing_storage.get('luns', [])]
        return None

    def get_lun_path_from_backend(self, name):
        """returns lun path matching name if found in backing_storage
           retruns None if not found
        """
        lun_paths = self.get_lun_paths_from_app()
        match = "/%s" % name
        for path in lun_paths:
            if path.endswith(match):
                return path
        return None

    def create_san_app_component(self):
        '''Create SAN application component'''
        required_options = ('name', 'size')
        for option in required_options:
            if self.parameters.get(option) is None:
                self.module.fail_json(msg='Error: "%s" is required to create san application.' % option)

        application_component = dict(
            name=self.parameters['name'],
            total_size=self.parameters['size'],
            lun_count=1                           # default value, may be overriden below
        )
        for attr in ('igroup_name', 'lun_count', 'storage_service'):
            value = self.na_helper.safe_get(self.parameters, ['san_application_template', attr])
            if value is not None:
                application_component[attr] = value
        for attr in ('os_type', 'qos_policy_group'):
            value = self.na_helper.safe_get(self.parameters, [attr])
            if value is not None:
                if attr == 'qos_policy_group':
                    attr = 'qos'
                    value = dict(policy=dict(name=value))
                application_component[attr] = value
        tiering = self.na_helper.safe_get(self.parameters, ['nas_application_template', 'tiering'])
        if tiering is not None:
            application_component['tiering'] = dict()
            for attr in ('control', 'policy', 'object_stores'):
                value = tiering.get(attr)
                if attr == 'object_stores' and value is not None:
                    value = [dict(name=x) for x in value]
                if value is not None:
                    application_component['tiering'][attr] = value
        return application_component

    def create_san_app_body(self):
        '''Create body for san template'''
        # TODO:
        # Should we support new_igroups?
        # It may raise idempotency issues if the REST call fails if the igroup already exists.
        # And we already have na_ontap_igroups.
        san = {
            'application_components': [self.create_san_app_component()],
        }
        for attr in ('protection_type',):
            value = self.na_helper.safe_get(self.parameters, ['san_application_template', attr])
            if value is not None:
                # we expect value to be a dict, but maybe an empty dict
                value = self.na_helper.filter_out_none_entries(value)
                if value:
                    san[attr] = value
        for attr in ('os_type',):
            value = self.na_helper.safe_get(self.parameters, [attr])
            if value is not None:
                san[attr] = value
        body, error = self.rest_app.create_application_body('san', san)
        return body, error

    def create_san_application(self):
        '''Use REST application/applications san template to create one or more LUNs'''
        body, error = self.create_san_app_body()
        self.fail_on_error(error)
        dummy, error = self.rest_app.create_application(body)
        self.fail_on_error(error)

    def delete_san_application(self):
        '''Use REST application/applications san template to delete one or more LUNs'''
        dummy, error = self.rest_app.delete_application()
        self.fail_on_error(error)

    def create_lun(self):
        """
        Create LUN with requested name and size
        """
        path = '/vol/%s/%s' % (self.parameters['flexvol_name'], self.parameters['name'])
        options = {'path': path,
                   'size': str(self.parameters['size']),
                   'space-reservation-enabled': str(self.parameters['space_reserve']),
                   'space-allocation-enabled': str(self.parameters['space_allocation']),
                   'use-exact-size': str(self.parameters['use_exact_size'])}
        if self.parameters.get('os_type') is not None:
            options['ostype'] = self.parameters['os_type']
        if self.parameters.get('qos_policy_group') is not None:
            options['qos-policy-group'] = self.parameters['qos_policy_group']
        lun_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'lun-create-by-size', **options)

        try:
            self.server.invoke_successfully(lun_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg="Error provisioning lun %s of size %s: %s"
                                  % (self.parameters['name'], self.parameters['size'], to_native(exc)),
                                  exception=traceback.format_exc())

    def delete_lun(self, path):
        """
        Delete requested LUN
        """
        lun_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'lun-destroy', **{'path': path,
                              'force': str(self.parameters['force_remove']),
                              'destroy-fenced-lun':
                                  str(self.parameters['force_remove_fenced'])})

        try:
            self.server.invoke_successfully(lun_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg="Error deleting lun %s: %s" % (path, to_native(exc)),
                                  exception=traceback.format_exc())

    def resize_lun(self, path):
        """
        Resize requested LUN.

        :return: True if LUN was actually re-sized, false otherwise.
        :rtype: bool
        """
        lun_resize = netapp_utils.zapi.NaElement.create_node_with_children(
            'lun-resize', **{'path': path,
                             'size': str(self.parameters['size']),
                             'force': str(self.parameters['force_resize'])})
        try:
            self.server.invoke_successfully(lun_resize, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            if to_native(exc.code) == "9042":
                # Error 9042 denotes the new LUN size being the same as the
                # old LUN size. This happens when there's barely any difference
                # in the two sizes. For example, from 8388608 bytes to
                # 8194304 bytes. This should go away if/when the default size
                # requested/reported to/from the controller is changed to a
                # larger unit (MB/GB/TB).
                return False
            else:
                self.module.fail_json(msg="Error resizing lun %s: %s" % (path, to_native(exc)),
                                      exception=traceback.format_exc())

        return True

    def set_lun_value(self, path, key, value):
        key_to_zapi = dict(
            qos_policy_group=('lun-set-qos-policy-group', 'qos-policy-group'),
            space_allocation=('lun-set-space-alloc', 'enable'),
            space_reserve=('lun-set-space-reservation-info', 'enable')
        )
        if key in key_to_zapi:
            zapi, option = key_to_zapi[key]
        else:
            self.module.fail_json(msg="option %s cannot be modified to %s" % (key, value))
        options = dict(path=path)
        if option == 'enable':
            options[option] = self.na_helper.get_value_for_bool(False, value)
        else:
            options[option] = value

        lun_set = netapp_utils.zapi.NaElement.create_node_with_children(zapi, **options)
        try:
            self.server.invoke_successfully(lun_set, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg="Error setting lun option %s: %s" % (key, to_native(exc)),
                                  exception=traceback.format_exc())
        return

    def modify_lun(self, path, modify):
        """
        update LUN properties (except size or name)
        """
        for key, value in modify.items():
            self.set_lun_value(path, key, value)

    def rename_lun(self, path, new_path):
        """
        rename LUN
        """
        lun_move = netapp_utils.zapi.NaElement.create_node_with_children(
            'lun-move', **{'path': path,
                           'new-path': new_path})
        try:
            self.server.invoke_successfully(lun_move, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg="Error moving lun %s: %s" % (path, to_native(exc)),
                                  exception=traceback.format_exc())

    def fail_on_error(self, error, stack=False):
        if error is None:
            return
        elements = dict(msg="Error: %s" % error)
        if stack:
            elements['stack'] = traceback.format_stack()
        self.module.fail_json(**elements)

    def apply(self):
        results = dict()
        warnings = list()
        netapp_utils.ems_log_event("na_ontap_lun", self.server)
        app_cd_action = None
        if self.rest_app:
            app_current, error = self.rest_app.get_application_uuid()
            self.fail_on_error(error)
            app_cd_action = self.na_helper.get_cd_action(app_current, self.parameters)
            if app_cd_action == 'create' and self.parameters.get('size') is None:
                self.module.fail_json(msg="size is a required parameter for create.")

        # For LUNs created using a SAN application, we're getting lun paths from the backing storage
        lun_path, from_lun_path = None, None
        from_name = self.parameters.get('from_name')
        if self.rest_app and app_cd_action is None and app_current:
            lun_path = self.get_lun_path_from_backend(self.parameters['name'])
            if from_name is not None:
                from_lun_path = self.get_lun_path_from_backend(from_name)

        if app_cd_action is None:
            # actions at LUN level
            current = self.get_lun(self.parameters['name'], lun_path)
            if current is not None and lun_path is None:
                lun_path = current['path']
            cd_action = self.na_helper.get_cd_action(current, self.parameters)
            modify, rename = None, None
            if cd_action == 'create' and from_name is not None:
                # create by renaming existing LUN, if it really exists
                old_lun = self.get_lun(from_name, from_lun_path)
                rename = self.na_helper.is_rename_action(old_lun, current)
                if rename is None:
                    self.module.fail_json(msg="Error renaming lun: %s does not exist" % from_name)
                if rename:
                    current = old_lun
                    if from_lun_path is None:
                        from_lun_path = current['path']
                    head, _sep, tail = from_lun_path.rpartition(from_name)
                    if tail:
                        self.module.fail_json(msg="Error renaming lun: %s does not match lun_path %s" % (from_name, from_lun_path))
                    lun_path = head + self.parameters['name']
                    results['renamed'] = True
                    cd_action = None
            if cd_action == 'create' and self.parameters.get('size') is None:
                self.module.fail_json(msg="size is a required parameter for create.")
            if cd_action is None and self.parameters['state'] == 'present':
                # we already handled rename if required
                current.pop('name', None)
                modify = self.na_helper.get_modified_attributes(current, self.parameters)
                results['modify'] = dict(modify)
            if cd_action and self.rest_app and app_cd_action is None and app_current:
                msg = 'This module does not support %s a LUN by name %s a SAN application.' %\
                      ('adding', 'to') if cd_action == 'create' else ('removing', 'from')
                warnings.append(msg)
                cd_action = None
                self.na_helper.changed = False

        if self.na_helper.changed and not self.module.check_mode:
            if app_cd_action == 'create':
                self.create_san_application()
            elif app_cd_action == 'delete':
                self.rest_app.delete_application()
            elif cd_action == 'create':
                self.create_lun()
            elif cd_action == 'delete':
                self.delete_lun(lun_path)
            else:
                if rename:
                    self.rename_lun(from_lun_path, lun_path)
                size_changed = False
                if modify and 'size' in modify:
                    # Ensure that size was actually changed. Please
                    # read notes in 'resize_lun' function for details.
                    size_changed = self.resize_lun(lun_path)
                    modify.pop('size')
                if modify:
                    self.modify_lun(lun_path, modify)
                if not modify and not rename:
                    # size may not have changed
                    self.na_helper.changed = size_changed

        results['changed'] = self.na_helper.changed
        self.module.exit_json(**results)


def main():
    lun = NetAppOntapLUN()
    lun.apply()


if __name__ == '__main__':
    main()
