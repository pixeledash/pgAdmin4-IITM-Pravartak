##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2025, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################
"""Implements Backup Utility"""

import json
import copy
import functools
import operator
import threading
import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, Response
from flask_babel import gettext
from pgadmin.user_login_check import pga_login_required
from pgadmin.misc.bgprocess.processes import BatchProcess, IProcessDesc
from pgadmin.utils import PgAdminModule, does_utility_exist, get_server, \
    filename_with_file_manager_path
from pgadmin.utils.ajax import make_json_response, bad_request, unauthorized
from pgadmin.utils.driver import get_driver

from config import PG_DEFAULT_DRIVER
# This unused import is required as API test cases will fail if we remove it,
# Have to identify the cause and then remove it.
from pgadmin.model import Server, SharedServer
from flask_security import current_user
from pgadmin.misc.bgprocess import escape_dquotes_process_arg
from pgadmin.utils.constants import MIMETYPE_APP_JS, SERVER_NOT_FOUND
from pgadmin.tools.grant_wizard import get_data

# set template path for sql scripts
MODULE_NAME = 'backup'
server_info = {}
MVIEW_STR = 'materialized view'
FOREIGN_TABLE_STR = 'foreign table'


class BackupModule(PgAdminModule):
    """
    class BackupModule():

        It is a utility which inherits PgAdminModule
        class and define methods to load its own
        javascript file.
    """

    LABEL = gettext('Backup')

    def show_system_objects(self):
        """
        return system preference objects
        """
        return self.pref_show_system_objects

    def get_exposed_url_endpoints(self):
        """
        Returns:
            list: URL endpoints for backup module
        """
        return ['backup.create_server_job', 'backup.create_object_job',
                'backup.utility_exists', 'backup.objects',
                'backup.schema_objects']


# Create blueprint for BackupModule class
blueprint = BackupModule(
    MODULE_NAME, __name__, static_url_path=''
)


class BACKUP():
    """
    Constants defined for Backup utilities
    """
    GLOBALS = 1
    SERVER = 2
    OBJECT = 3


class BackupMessage(IProcessDesc):
    """
    BackupMessage(IProcessDesc)

    Defines the message shown for the backup operation.
    """

    def __init__(self, _type, _sid, _bfile, *_args, **_kwargs):
        self.backup_type = _type
        self.sid = _sid
        self.bfile = _bfile
        self.database = _kwargs['database'] if 'database' in _kwargs else None
        self.cmd = ''
        self.args_str = "{0} ({1}:{2})"

        def cmd_arg(x):
            if x:
                x = x.replace('\\', '\\\\')
                x = x.replace('"', '\\"')
                x = x.replace('""', '\\"')
                return ' "' + x + '"'
            return ''

        for arg in _args:
            if arg and len(arg) >= 2 and arg.startswith('--'):
                self.cmd += ' ' + arg
            else:
                self.cmd += cmd_arg(arg)

    def get_server_name(self):
        s = get_server(self.sid)

        if s is None:
            return gettext("Not available")

        from pgadmin.utils.driver import get_driver
        driver = get_driver(PG_DEFAULT_DRIVER)
        manager = driver.connection_manager(self.sid)

        host = manager.local_bind_host if manager.use_ssh_tunnel else s.host
        port = manager.local_bind_port if manager.use_ssh_tunnel else s.port

        return "{0} ({1}:{2})".format(s.name, host, port)

    @property
    def type_desc(self):
        if self.backup_type == BACKUP.OBJECT:
            return gettext("Backing up an object on the server")
        if self.backup_type == BACKUP.GLOBALS:
            return gettext("Backing up the global objects")
        elif self.backup_type == BACKUP.SERVER:
            return gettext("Backing up the server")
        else:
            # It should never reach here.
            return gettext("Unknown Backup")

    @property
    def message(self):
        server_name = self.get_server_name()

        if self.backup_type == BACKUP.OBJECT:
            return gettext(
                "Backing up an object on the server '{0}' "
                "from database '{1}'"
            ).format(server_name, self.database)
        if self.backup_type == BACKUP.GLOBALS:
            return gettext("Backing up the global objects on "
                           "the server '{0}'").format(
                server_name
            )
        elif self.backup_type == BACKUP.SERVER:
            return gettext("Backing up the server '{0}'").format(
                server_name
            )
        else:
            # It should never reach here.
            return "Unknown Backup"

    def details(self, cmd, args):
        server_name = self.get_server_name()
        backup_type = gettext("Backup")
        if self.backup_type == BACKUP.OBJECT:
            backup_type = gettext("Backup Object")
        elif self.backup_type == BACKUP.GLOBALS:
            backup_type = gettext("Backup Globals")
        elif self.backup_type == BACKUP.SERVER:
            backup_type = gettext("Backup Server")

        return {
            "message": self.message,
            "cmd": cmd + self.cmd,
            "server": server_name,
            "object": self.database,
            "type": backup_type,
        }


@blueprint.route("/")
@pga_login_required
def index():
    return bad_request(errormsg=gettext("This URL cannot be called directly."))


@blueprint.route("/backup.js")
@pga_login_required
def script():
    """render own javascript"""
    return Response(
        response=render_template(
            "backup/js/backup.js", _=_
        ),
        status=200,
        mimetype=MIMETYPE_APP_JS
    )


def _get_args_params_values(data, conn, backup_obj_type, backup_file, server,
                            manager):
    """
    Used internally by create_backup_objects_job. This function will create
    the required args and params for the job.
    :param data: input data
    :param conn: connection obj
    :param backup_obj_type: object type
    :param backup_file: file name
    :param server: server obj
    :param manager: connection manager
    :return: args array
    """
    from pgadmin.utils.driver import get_driver
    driver = get_driver(PG_DEFAULT_DRIVER)

    host, port = (manager.local_bind_host, str(manager.local_bind_port)) \
        if manager.use_ssh_tunnel else (server.host, str(server.port))
    args = [
        '--file',
        backup_file,
        '--host',
        host,
        '--port',
        port,
        '--username',
        manager.user,
        '--no-password'
    ]

    def set_param(key, param, assertion=True):
        if not assertion:
            return
        if data.get(key, None):
            args.append(param)

    def set_value(key, param, default_value=None, assertion=True):
        if not assertion:
            return
        val = data.get(key, default_value)
        if val:
            if isinstance(val, list):
                for c_val in val:
                    args.append(param)
                    args.append(c_val)
                return
            args.append(param)
            args.append(val)

    if backup_obj_type != 'objects':
        args.append('--database')
        args.append(server.maintenance_db)

    if backup_obj_type == 'globals':
        args.append('--globals-only')

    set_value('role', '--role')

    if backup_obj_type == 'objects' and data.get('format', None):
        args.extend(['--format={0}'.format({
            'custom': 'c',
            'tar': 't',
            'plain': 'p',
            'directory': 'd'
        }[data['format']])])

        # --blobs is deprecated from v16
        if manager.version >= 160000:
            set_param('blobs', '--large-objects',
                      data['format'] in ['custom', 'tar'])
        else:
            set_param('blobs', '--blobs', data['format'] in ['custom', 'tar'])
        set_value('ratio', '--compress')

    set_value('encoding', '--encoding')
    set_value('no_of_jobs', '--jobs')

    # Data options
    set_param('only_data', '--data-only',
              data.get('only_data', None))
    set_param('only_schema', '--schema-only',
              data.get('only_schema', None) and
              not data.get('only_data', None))
    set_param('only_tablespaces', '--tablespaces-only',
              data.get('only_tablespaces', None))
    set_param('only_roles', '--roles-only',
              data.get('only_roles', None))

    # Sections
    set_param('pre_data', '--section=pre-data')
    set_param('data', '--section=data')
    set_param('post_data', '--section=post-data')

    # Do not Save
    set_param('dns_owner', '--no-owner')
    set_param('dns_privilege', '--no-privileges')
    set_param('dns_tablespace', '--no-tablespaces')
    set_param('dns_unlogged_tbl_data', '--no-unlogged-table-data')
    set_param('dns_comments', '--no-comments', manager.version >= 110000)
    set_param('dns_publications', '--no-publications',
              manager.version >= 110000)
    set_param('dns_subscriptions', '--no-subscriptions',
              manager.version >= 110000)
    set_param('dns_security_labels', '--no-security-labels',
              manager.version >= 110000)
    set_param('dns_toast_compression', '--no-toast-compression',
              manager.version >= 140000)
    set_param('dns_table_access_method', '--no-table-access-method',
              manager.version >= 150000)
    set_param('dns_no_role_passwords', '--no-role-passwords')

    # Query Options
    set_param('use_insert_commands', '--inserts')
    set_value('max_rows_per_insert', '--rows-per-insert', None,
              manager.version >= 120000)
    set_param('on_conflict_do_nothing', '--on-conflict-do-nothing',
              manager.version >= 120000)
    set_param('include_create_database', '--create')
    set_param('include_drop_database', '--clean')
    set_param('if_exists', '--if-exists')

    # Table options
    set_param('use_column_inserts', '--column-inserts')
    set_param('load_via_partition_root', '--load-via-partition-root',
              manager.version >= 110000)
    set_param('enable_row_security', '--enable-row-security')
    set_value('exclude_table_data', '--exclude-table-data')
    set_value('table_and_children', '--table-and-children', None,
              manager.version >= 160000)
    set_value('exclude_table_and_children', '--exclude-table-and-children',
              None, manager.version >= 160000)
    set_value('exclude_table_data_and_children',
              '--exclude-table-data-and-children', None,
              manager.version >= 160000)
    set_value('exclude_table', '--exclude-table')

    # Disable options
    set_param('disable_trigger', '--disable-triggers',
              data.get('only_data', None) and
              data.get('format', '') == 'plain')
    set_param('disable_quoting', '--disable-dollar-quoting')

    # Misc Options
    set_param('verbose', '--verbose')
    set_param('dqoute', '--quote-all-identifiers')
    set_param('use_set_session_auth', '--use-set-session-authorization')
    set_value('exclude_schema', '--exclude-schema')
    set_value('extra_float_digits', '--extra-float-digits', None,
              manager.version >= 120000)
    set_value('lock_wait_timeout', '--lock-wait-timeout')
    set_value('exclude_database', '--exclude-database', None,
              manager.version >= 160000)

    args.extend(
        functools.reduce(operator.iconcat, map(
            lambda s: ['--schema', r'{0}'.format(driver.qtIdent(conn, s).
                                                 replace('"', '\"'))],
            data.get('schemas', [])), []
        )
    )

    args.extend(
        functools.reduce(operator.iconcat, map(
            lambda t: ['--table',
                       r'{0}'.format(driver.qtIdent(conn, t[0], t[1])
                                     .replace('"', '\"'))],
            data.get('tables', [])), []
        )
    )

    if 'objects' in data:
        selected_objects = data.get('objects', {})
        for _key in selected_objects:
            param = 'schema' if _key == 'schema' else 'table'
            args.extend(
                functools.reduce(operator.iconcat, map(
                    lambda s: [f'--{param}',
                               r'{0}.{1}'.format(
                                   driver.qtIdent(conn, s['schema']).replace(
                                       '"', '\"'),
                                   driver.qtIdent(conn, s['name']).replace(
                                       '"', '\"')) if type(
                                   s) is dict else driver.qtIdent(
                                   conn, s).replace('"', '\"')],
                    selected_objects[_key] or []), [])
            )

    return args


class BackupSchedulerJob:
    """Class to represent a scheduled backup job"""
    
    def __init__(self, sid, data, schedule_type, start_time):
        self.sid = sid
        self.data = data  # Contains all backup settings including format, filename etc
        self.schedule_type = schedule_type
        self.start_time = start_time
        self.last_run = None
    
    def should_run(self):
        """Check if the job should run now based on schedule"""
        now = datetime.now()
        
        # Don't run if start time hasn't been reached yet
        if now < self.start_time:
            print(f"Job {self.sid} not started yet, current time: {now}, start time: {self.start_time}")
            return False
            
        if self.last_run:
            if self.schedule_type == 'one_time':
                return False
            elif self.schedule_type == 'daily':
                next_run = self.last_run.replace(
                    hour=self.start_time.hour,
                    minute=self.start_time.minute,
                    second=self.start_time.second
                ) + timedelta(days=1)
                return now >= next_run
            elif self.schedule_type == 'weekly':
                next_run = self.last_run.replace(
                    hour=self.start_time.hour,
                    minute=self.start_time.minute,
                    second=self.start_time.second
                ) + timedelta(days=7)
                return now >= next_run
            elif self.schedule_type == 'monthly':
                # Get the same day next month
                if self.last_run.month == 12:
                    next_month = 1
                    next_year = self.last_run.year + 1
                else:
                    next_month = self.last_run.month + 1
                    next_year = self.last_run.year
                    
                next_run = self.last_run.replace(
                    year=next_year,
                    month=next_month,
                    hour=self.start_time.hour,
                    minute=self.start_time.minute,
                    second=self.start_time.second
                )
                return now >= next_run
        else:
            # First run
            return True

class BackupScheduler:
    """Scheduler service for backup jobs"""
    
    def __init__(self):
        self.jobs = {}
        self.thread = None
        self.running = False
        self.app = None
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
    
    def add_job(self, sid, data, schedule_type, start_time):
        """Add a new scheduled backup job"""
        job = BackupSchedulerJob(sid, data, schedule_type, start_time)
        if sid not in self.jobs:
            self.jobs[sid] = []
        self.jobs[sid].append(job)
        
        if not self.running:
            self.start()
    
    def start(self):
        """Start the scheduler thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """Stop the scheduler thread"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _run(self):
        """Main scheduler loop"""
        from flask import current_app
        
        while self.running:
            try:
                # Use app object if available, otherwise try current_app
                app_ctx = self.app.app_context() if self.app else current_app.app_context()
                
                with app_ctx:
                    now = datetime.now()
                    for sid in list(self.jobs.keys()):
                        for job in self.jobs[sid]:
                            if job.should_run():
                                try:
                                    create_backup_objects_job(sid, job.data)
                                    job.last_run = now
                                except Exception as e:
                                    current_app.logger.exception(
                                        f"Error executing scheduled backup for server {sid}: {str(e)}"
                                    )
                                    
                time.sleep(60)  # Check every minute
                    
            except Exception as e:
                print(f"Error in backup scheduler: {str(e)}")
                time.sleep(60)

# Initialize the scheduler
backup_scheduler = BackupScheduler()

@blueprint.route(
    '/job/<int:sid>', methods=['POST'], endpoint='create_server_job'
)
@blueprint.route(
    '/job/<int:sid>/object', methods=['POST'], endpoint='create_object_job'
)
@pga_login_required
def create_backup_objects_job(sid, scheduled_data=None):
    """
    Args:
        sid: Server ID
        scheduled_data: Data for scheduled backup (optional)

    Returns:
        None
    """
    try:
        data = scheduled_data if scheduled_data else json.loads(request.data)
        backup_obj_type = data.get('type', 'objects')

        # Handle scheduler if enabled
        if not scheduled_data and data.get('enable_scheduler'):
            try:
                schedule_type = data.get('schedule_type')
                # start_date_time = data.get('start_date_time')
                start_date_time = "2025-03-25 01:26:00"
                if not start_date_time:
                    return make_json_response(
                        success=0,
                        errormsg='Start date and time is required for scheduling'
                    )
                
                try:
                    # Remove timezone offset if present
                    if '+' in start_date_time:
                        start_date_time = start_date_time.split('+')[0].strip()
                    elif '-' in start_date_time and start_date_time.count('-') > 2:
                        start_date_time = start_date_time.rsplit('-', 1)[0].strip()
                    
                    start_datetime = datetime.strptime(
                        start_date_time,
                        "%Y-%m-%d %H:%M:%S"
                    )
                    
                    # Create a copy of data for the scheduler
                    backup_config = copy.deepcopy(data)
                    
                    # Remove scheduler-specific fields but keep backup settings
                    scheduler_fields = ['enable_scheduler', 'schedule_type', 'start_date_time']
                    for field in scheduler_fields:
                        if field in backup_config:
                            del backup_config[field]
                    
                    # Add job to scheduler with backup configuration
                    backup_scheduler.add_job(
                        sid=sid,
                        data=backup_config,
                        schedule_type=schedule_type,
                        start_time=start_datetime
                    )
                    
                    return make_json_response(
                        data={'message': 'Backup scheduled successfully', 'Success': 1}
                    )
                except ValueError as e:
                    return make_json_response(
                        success=0,
                        errormsg=f'Invalid datetime format: {str(e)}'
                    )
            except Exception as e:
                current_app.logger.exception(
                    f"Error scheduling backup: {str(e)}"
                )
                return make_json_response(
                    success=0,
                    errormsg=f'Error scheduling backup: {str(e)}'
                )

        # Continue with immediate backup process
        try:
            backup_file = filename_with_file_manager_path(
                data['file'], (data.get('format', '') != 'directory'))
        except PermissionError as e:
            return unauthorized(errormsg=str(e))
        except Exception as e:
            return bad_request(errormsg=str(e))

        # Fetch the server details like hostname, port, roles etc
        server = get_server(sid)

        if server is None:
            return make_json_response(
                success=0,
                errormsg=SERVER_NOT_FOUND
            )

        # To fetch MetaData for the server
        driver = get_driver(PG_DEFAULT_DRIVER)
        manager = driver.connection_manager(server.id)
        conn = manager.connection()
        
        if not conn.connected():
            return make_json_response(
                success=0,
                errormsg=gettext("Please connect to the server first.")
            )

        utility = manager.utility('backup') if backup_obj_type == 'objects' \
            else manager.utility('backup_server')

        ret_val = does_utility_exist(utility)
        if ret_val:
            return make_json_response(
                success=0,
                errormsg=ret_val
            )

        args = _get_args_params_values(
            data, conn, backup_obj_type, backup_file, server, manager)

        escaped_args = [
            escape_dquotes_process_arg(arg) for arg in args
        ]
        
        try:
            bfile = data['file'].encode('utf-8') \
                if hasattr(data['file'], 'encode') else data['file']
                
            if backup_obj_type == 'objects':
                args.append(data['database'])
                escaped_args.append(data['database'])
                p = BatchProcess(
                    desc=BackupMessage(
                        BACKUP.OBJECT, server.id, bfile,
                        *args,
                        database=data['database']
                    ),
                    cmd=utility, args=escaped_args, manager_obj=manager
                )
            else:
                p = BatchProcess(
                    desc=BackupMessage(
                        BACKUP.SERVER if backup_obj_type != 'globals'
                        else BACKUP.GLOBALS,
                        server.id, bfile,
                        *args
                    ),
                    cmd=utility, args=escaped_args, manager_obj=manager
                )

            p.set_env_variables(server)
            p.start()
            
            return make_json_response(
                data={'job_id': p.id, 'desc': p.desc.message, 'Success': 1}
            )
            
        except Exception as e:
            current_app.logger.exception(e)
            return make_json_response(
                status=410,
                success=0,
                errormsg=str(e)
            )
            
    except Exception as e:
        current_app.logger.exception(e)
        return make_json_response(
            status=410,
            success=0,
            errormsg=str(e)
        )


@blueprint.route(
    '/utility_exists/<int:sid>/<backup_obj_type>', endpoint='utility_exists'
)
@pga_login_required
def check_utility_exists(sid, backup_obj_type):
    """
    This function checks the utility file exist on the given path.

    Args:
        sid: Server ID
        backup_obj_type: Type of the object
    Returns:
        None
    """
    server = get_server(sid)

    if server is None:
        return make_json_response(
            success=0,
            errormsg=SERVER_NOT_FOUND
        )

    from pgadmin.utils.driver import get_driver
    driver = get_driver(PG_DEFAULT_DRIVER)
    manager = driver.connection_manager(server.id)

    utility = manager.utility('backup') if backup_obj_type == 'objects' \
        else manager.utility('backup_server')

    ret_val = does_utility_exist(utility)
    if ret_val:
        return make_json_response(
            success=0,
            errormsg=ret_val
        )

    return make_json_response(success=1)


@blueprint.route(
    '/objects/<int:sid>/<int:did>', endpoint='objects'
)
@blueprint.route(
    '/objects/<int:sid>/<int:did>/<int:scid>', endpoint='schema_objects'
)
@pga_login_required
def objects(sid, did, scid=None):
    """
    This function returns backup objects

    Args:
        sid: Server ID
        did: database ID
        scid: schema ID
    Returns:
        list of objects
    """
    server = get_server(sid)

    if server is None:
        return make_json_response(
            success=0,
            errormsg=SERVER_NOT_FOUND
        )

    from pgadmin.utils.driver import get_driver
    from pgadmin.utils.ajax import precondition_required

    server_info = {}
    server_info['manager'] = get_driver(PG_DEFAULT_DRIVER) \
        .connection_manager(sid)
    server_info['conn'] = server_info['manager'].connection(
        did=did)
    # If DB not connected then return error to browser
    if not server_info['conn'].connected():
        return precondition_required(
            gettext("Connection to the server has been lost.")
        )

    # Set template path for sql scripts
    server_info['server_type'] = server_info['manager'].server_type
    server_info['version'] = server_info['manager'].version
    if server_info['server_type'] == 'pg':
        server_info['template_path'] = 'grant_wizard/pg/#{0}#'.format(
            server_info['version'])
    elif server_info['server_type'] == 'ppas':
        server_info['template_path'] = 'grant_wizard/ppas/#{0}#'.format(
            server_info['version'])

    res, _, empty_schema_list = get_data(sid, did, scid,
                                         'schema' if scid else 'database',
                                         server_info, True)

    tree_data = {
        'table': [],
        'view': [],
        MVIEW_STR: [],
        FOREIGN_TABLE_STR: [],
        'sequence': []
    }

    schema_group = {}

    for data in res:
        obj_type = data['object_type'].lower()
        if obj_type in ['table', 'view', MVIEW_STR, FOREIGN_TABLE_STR,
                        'sequence']:

            if data['nspname'] not in schema_group:
                schema_group[data['nspname']] = {
                    'id': data['nspname'],
                    'name': data['nspname'],
                    'icon': 'icon-schema',
                    'children': copy.deepcopy(tree_data),
                    'is_schema': True,
                }
            icon_data = {
                MVIEW_STR: 'icon-mview',
                FOREIGN_TABLE_STR: 'icon-foreign_table'
            }
            icon = icon_data[obj_type] if obj_type in icon_data \
                else data['icon']
            schema_group[data['nspname']]['children'][obj_type].append({
                'id': f'{data["nspname"]}_{data["name"]}',
                'name': data['name'],
                'icon': icon,
                'schema': data['nspname'],
                'type': obj_type,
                '_name': '{0}.{1}'.format(data['nspname'], data['name'])
            })

    schema_group = [dt for k, dt in schema_group.items()]
    for ch in schema_group:
        children = []
        for obj_type, data in ch['children'].items():
            if data:
                icon_data = {
                    MVIEW_STR: 'icon-coll-mview',
                    FOREIGN_TABLE_STR: 'icon-coll-foreign_table'
                }
                icon = icon_data[obj_type] if obj_type in icon_data \
                    else f'icon-coll-{obj_type.lower()}',
                children.append({
                    'id': f'{ch["id"]}_{obj_type}',
                    'name': f'{obj_type.title()}s',
                    'icon': icon,
                    'children': data,
                    'type': obj_type,
                    'is_collection': True,
                })

        ch['children'] = children

    for empty_schema in empty_schema_list:
        schema_group.append({
            'id': empty_schema,
            'name': empty_schema,
            'icon': 'icon-schema',
            'children': [],
            'is_schema': True,
        })
    return make_json_response(
        data=schema_group,
        success=200
    )

def create_module(app, **kwargs):
    # Register blueprint
    app.register_blueprint(blueprint)
    
    # Initialize the scheduler with the app
    backup_scheduler.init_app(app)
