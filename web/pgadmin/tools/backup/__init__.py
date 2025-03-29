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
import calendar
import os
import logging
import traceback
from typing import Dict, Any, List, Optional

# Try importing schedule package, but don't fail if not available
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    logging.warning("Schedule package not available. Some backup scheduling features will be disabled.")

import psycopg2
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from flask import render_template, request, current_app, Response, Flask
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
from flask_security import current_user, login_required
from pgadmin.misc.bgprocess import escape_dquotes_process_arg
from pgadmin.utils.constants import MIMETYPE_APP_JS, SERVER_NOT_FOUND
from pgadmin.tools.grant_wizard import get_data

# set template path for sql scripts
MODULE_NAME = 'backup'
server_info = {}
MVIEW_STR = 'materialized view'
FOREIGN_TABLE_STR = 'foreign table'

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PgAdminBackupScheduler')

# SQLAlchemy Base for ORM
Base = declarative_base()

class BackupSchedule(Base):
    """
    ORM model for storing backup schedule configurations
    """
    __tablename__ = 'backup_schedules'

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, nullable=False)
    file_directory = Column(String, nullable=False)
    is_enabled = Column(Boolean, default=True)
    backup_frequency = Column(String, nullable=False)  # e.g., 'daily', 'weekly', 'monthly'
    start_time = Column(String, nullable=False)  # Format: 'HH:MM'
    repeat_days = Column(String)  # Comma-separated day names or numbers
    repeat_months = Column(String)  # Comma-separated month names or numbers


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


@blueprint.route('/test_scheduler/<int:sid>', methods=['GET'])
@pga_login_required
def test_scheduler(sid):
    """Test endpoint to check scheduler status"""
    print(f"Test scheduler endpoint called for server {sid}")
    status = {
        'running': backup_scheduler.running,
        'initialized': backup_scheduler.initialized,
        'thread_alive': backup_scheduler.thread.is_alive() if backup_scheduler.thread else False,
        'job_count': sum(len(jobs) for jobs in backup_scheduler.jobs.values()),
        'jobs': {}
    }
    
    # Add job details
    for server_id, job_list in backup_scheduler.jobs.items():
        status['jobs'][str(server_id)] = []
        for job in job_list:
            job_info = {
                'type': job.schedule_type,
                'last_run': job.last_run.isoformat() if job.last_run else None,
                'next_run': job.next_run.isoformat() if job.next_run else None,
                'run_count': job.run_count,
                'last_status': job.last_status
            }
            status['jobs'][str(server_id)].append(job_info)
    
    print(f"Scheduler status: {status}")
    return make_json_response(data=status)


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
        self.last_status = None  # Track success/failure
        self.next_run = start_time  # Initialize next_run to start_time
        self.run_count = 0  # Count of successful runs
        logger.debug(f"Created new backup job: type={schedule_type}, start_time={start_time}")
    
    def should_run(self, now=None):
        """Check if the job should run now based on schedule"""
        if now is None:
            now = datetime.now()
            
        # Log debug info
        logger.debug(f"Checking job schedule: now={now}, next_run={self.next_run}, last_run={self.last_run}")
        
        # Don't run if next_run hasn't been reached yet
        if now < self.next_run:
            logger.debug(f"Job not ready yet: waiting until {self.next_run}")
            return False
            
        # For one-time jobs, only run once
        if self.schedule_type == 'one_time' and self.last_run:
            logger.debug(f"One-time job already ran at {self.last_run}")
            return False
            
        return True
        
    def calculate_next_run(self):
        """Calculate the next run time based on schedule type"""
        if not self.last_run:
            self.next_run = self.start_time
            return
            
        if self.schedule_type == 'one_time':
            self.next_run = None
        elif self.schedule_type == 'daily':
            self.next_run = self.last_run.replace(
                hour=self.start_time.hour,
                minute=self.start_time.minute,
                second=self.start_time.second
            ) + timedelta(days=1)
        elif self.schedule_type == 'weekly':
            self.next_run = self.last_run.replace(
                hour=self.start_time.hour,
                minute=self.start_time.minute,
                second=self.start_time.second
            ) + timedelta(days=7)
        elif self.schedule_type == 'monthly':
            # Get the same day next month
            if self.last_run.month == 12:
                next_month = 1
                next_year = self.last_run.year + 1
            else:
                next_month = self.last_run.month + 1
                next_year = self.last_run.year
                
            try:
                self.next_run = self.last_run.replace(
                    year=next_year,
                    month=next_month,
                    hour=self.start_time.hour,
                    minute=self.start_time.minute,
                    second=self.start_time.second
                )
            except ValueError:
                # Handle case for months with different number of days
                last_day = calendar.monthrange(next_year, next_month)[1]
                self.next_run = datetime(
                    year=next_year,
                    month=next_month,
                    day=min(self.last_run.day, last_day),
                    hour=self.start_time.hour,
                    minute=self.start_time.minute,
                    second=self.start_time.second
                )
        
        logger.debug(f"Next run calculated: {self.next_run}")

class BackupScheduler:
    """Scheduler service for backup jobs"""
    
    def __init__(self, database_url=None):
        """Initialize the scheduler"""
        self.app = None
        self.jobs = {}  # Dictionary to store jobs by server ID
        self.thread = None
        self.running = False
        self.initialized = False
        self.last_check_time = None
        self.status_log = []
        self.logger = logger
        
        if not SCHEDULE_AVAILABLE:
            self.logger.warning("Schedule package not available. Backup scheduling features will be disabled.")
            return
            
        # Initialize database if URL provided
        if database_url:
            self.engine = create_engine(database_url)
            Base.metadata.create_all(self.engine)
        
        logger.info("=== BackupScheduler Initialized ===")

    def init_app(self, app):
        """Initialize with Flask app"""
        logger.info("\n=== Initializing Backup Scheduler ===")
        self.app = app
        
        # Setup logging
        if app and hasattr(app, 'logger'):
            self.logger = app.logger
            self.logger.debug("Initializing backup scheduler with Flask app")
        else:
            self.logger = logger
            self.logger.debug("Initializing backup scheduler with standalone logger")
        
        # Mark as initialized
        self.initialized = True
        logger.info("Backup scheduler initialized with app")
        
        logger.info("=== Backup Scheduler Initialization Complete ===\n")

    def _validate_backup_config(self, config: Dict[str, Any]) -> bool:
        """Validate backup configuration"""
        # Check for required fields
        required_fields = {
            'file': 'Backup file path',
            'enable_scheduler': 'Enable scheduler flag'
        }
        
        for field, description in required_fields.items():
            if field not in config:
                self.logger.error(f"Missing required configuration: {description}")
                return False
        
        # Time format validation
        try:
            # Remove timezone offset if present
            start_time = config.get('start_date_time')
            if start_time:
                if '+' in start_time:
                    start_time = start_time.split('+')[0].strip()
                elif '-' in start_time and start_time.count('-') > 2:
                    start_time = start_time.rsplit('-', 1)[0].strip()
                
                datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            self.logger.error(f"Invalid time format: {config.get('start_date_time')}")
            return False
        
        return True

    def add_job(self, sid, data, schedule_type, start_time):
        """Add a new scheduled backup job"""
        if not SCHEDULE_AVAILABLE:
            self.logger.error("Cannot add backup job: schedule package not available")
            return False
        
        # Add server_id to data for validation
        data['server_id'] = sid
        
        # Create a copy of data for validation
        validation_data = copy.deepcopy(data)
        validation_data['enable_scheduler'] = True  # Add this for validation
        
        if not self._validate_backup_config(validation_data):
            return False
        
        self.logger.debug(f"Adding new job: server={sid}, type={schedule_type}, start_time={start_time}")
        
        job = BackupSchedulerJob(sid, data, schedule_type, start_time)
        if sid not in self.jobs:
            self.jobs[sid] = []
        self.jobs[sid].append(job)
        
        # Store in database if available
        if hasattr(self, 'engine'):
            with Session(self.engine) as session:
                try:
                    new_schedule = BackupSchedule(
                        server_id=sid,
                        file_directory=os.path.dirname(data['file']),
                        is_enabled=True,
                        backup_frequency=schedule_type,
                        start_time=start_time.strftime('%H:%M'),
                        repeat_days=data.get('repeat_days', ''),
                        repeat_months=data.get('repeat_months', '')
                    )
                    session.add(new_schedule)
                    session.commit()
                except Exception as e:
                    self.logger.error(f"Error storing schedule in database: {e}")
                    session.rollback()
        
        self.logger.info(
            f"New {schedule_type} backup job added for server {sid}, "
            f"starting at {start_time.isoformat()}"
        )
        
        if not self.running and self.initialized:
            self.logger.debug("Starting scheduler as it's not running")
            self.start()
        elif not self.initialized:
            self.logger.warning("Scheduler not initialized yet, job will be picked up when it starts")
        
        return True

    def start(self):
        """Start the scheduler thread"""
        if not self.initialized:
            self.logger.error("Cannot start scheduler - not initialized")
            return False
        
        self.logger.info("\n=== Starting Backup Scheduler Thread ===")
        self.logger.info(f"Current state: running={self.running}, initialized={self.initialized}")
        
        if self.running:
            self.logger.info("Scheduler already running")
            return True
        
        try:
            self.running = True
            self.logger.debug("Creating BackupScheduler thread...")
            
            # Create and configure the thread
            self.thread = threading.Thread(target=self._run, name="BackupScheduler")
            self.thread.daemon = False  # Make it a non-daemon thread
            self.thread.start()
            
            # Wait for thread to start
            time.sleep(0.5)
            
            if self.thread.is_alive():
                self.logger.info("Backup scheduler thread started successfully")
                self.logger.info(f"Thread ID: {self.thread.ident}")
                self.logger.info(f"Thread name: {self.thread.name}")
                self.logger.info(f"Thread daemon: {self.thread.daemon}")
                return True
            else:
                self.running = False
                self.logger.error("Failed to start scheduler thread - thread not alive")
                return False
        
        except Exception as e:
            self.logger.critical(f"Scheduler start failed: {e}")
            self.logger.critical(traceback.format_exc())
            self.running = False
            self.thread = None
            return False

    def stop(self):
        """Stop the scheduler thread"""
        if self.running:
            self.logger.debug("Stopping backup scheduler thread")
            self.running = False
            if self.thread:
                self.thread.join(timeout=1)
                self.logger.info("Backup scheduler thread stopped")

    def _run(self):
        """Main scheduler loop"""
        self.logger.info("=== Backup Scheduler Thread Starting ===")
        self.logger.info(f"Current time: {datetime.now()}")
        self.logger.info(f"Number of jobs: {sum(len(jobs) for jobs in self.jobs.values())}")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        check_interval = 30  # Check every minute
        
        while self.running:
            try:
                with self.app.app_context():
                    current_time = datetime.now()
                    self.last_check_time = current_time
                    
                    # Log current state
                    self.logger.info(f"\n=== Scheduler Check at {current_time} ===")
                    self.logger.info(f"Running: {self.running}")
                    self.logger.info(f"Thread alive: {self.thread.is_alive() if self.thread else False}")
                    
                    job_count = sum(len(jobs) for jobs in self.jobs.values())
                    self.logger.info(f"Checking {job_count} scheduled backup jobs")
                    
                    # Process each job
                    for sid, job_list in self.jobs.items():
                        self.logger.info(f"\nChecking jobs for server {sid}:")
                        for job in job_list:
                            self.logger.info(f"Job type: {job.schedule_type}")
                            self.logger.info(f"Last run: {job.last_run}")
                            self.logger.info(f"Next run: {job.next_run}")
                            self.logger.info(f"Current time: {current_time}")
                            
                            if job.should_run():
                                self.logger.info(f"Job should run now!")
                                try:
                                    # Execute backup
                                    self._execute_backup(job)
                                    job.last_run = current_time
                                    job.run_count += 1
                                    job.calculate_next_run()
                                    self.logger.info(f"Backup job completed successfully: server={sid}, type={job.schedule_type}")
                                    self.logger.info(f"Next run scheduled for: {job.next_run}")
                                except Exception as e:
                                    self.logger.error(f"Error executing backup job: {e}")
                                    self.logger.error(traceback.format_exc())
                                    job.last_status = 'failed'
                            else:
                                self.logger.info("Job not ready to run yet")
                    
                    # Reset error count on successful iteration
                    consecutive_errors = 0
                    
            except Exception as e:
                consecutive_errors += 1
                error_msg = f"Error in scheduler loop (attempt {consecutive_errors}): {str(e)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.critical("Too many consecutive errors. Stopping scheduler.")
                    self.running = False
                    break
                
                time.sleep(10)
            
            # Sleep for the check interval
            self.logger.debug(f"Sleeping for {check_interval} seconds...")
            time.sleep(check_interval)
        
        self.logger.info("=== Backup Scheduler Thread Exiting ===")

    def _execute_backup(self, job):
        """Execute a backup job"""
        try:
            # Create a mock request context for the backup operation
            with self.app.test_request_context():
                # Set up a mock user for authentication
                from flask_security import current_user
                from pgadmin.model import User, Role
                from flask_login import login_user
                from flask import session
                
                # Get the first admin user by checking role membership
                admin_role = Role.query.filter_by(id=1).first()
                if admin_role:
                    admin_user = User.query.filter(User.roles.contains(admin_role)).first()
                    if admin_user:
                        # Properly set up the user context
                        login_user(admin_user)
                        current_user._get_current_object = lambda: admin_user
                        
                        # Set up session with required authentication info
                        session['auth_source_manager'] = {
                            'current_source': 'internal',
                            'current_user': admin_user.username,
                            'user_id': admin_user.id
                        }
                        
                        self.logger.debug(f"Set up user context for {admin_user.username}")
                    else:
                        raise Exception("No admin user found")
                else:
                    raise Exception("Admin role not found")
                
                # Get server details
                server = get_server(job.sid)
                if not server:
                    raise Exception(f"Server {job.sid} not found")
                
                # Get connection manager
                driver = get_driver(PG_DEFAULT_DRIVER)
                manager = driver.connection_manager(server.id)
                
                # Connect to the server
                conn = manager.connection()
                if not conn.connected():
                    self.logger.debug("Attempting to connect to server...")
                    conn.connect()
                    if not conn.connected():
                        raise Exception("Failed to connect to the server")
                    self.logger.debug("Successfully connected to server")
                
                # Get backup utility
                backup_obj_type = job.data.get('type', 'objects')
                utility = manager.utility('backup') if backup_obj_type == 'objects' else manager.utility('backup_server')
                
                # Check if utility exists
                ret_val = does_utility_exist(utility)
                if ret_val:
                    raise Exception(ret_val)
                
                # Get backup file path
                backup_file = filename_with_file_manager_path(
                    job.data['file'], (job.data.get('format', '') != 'directory'))
                
                # Get backup arguments
                args = _get_args_params_values(
                    job.data, conn, backup_obj_type, backup_file, server, manager)
                
                escaped_args = [escape_dquotes_process_arg(arg) for arg in args]
                
                # Create backup process
                bfile = job.data['file'].encode('utf-8') if hasattr(job.data['file'], 'encode') else job.data['file']
                
                if backup_obj_type == 'objects':
                    args.append(job.data['database'])
                    escaped_args.append(job.data['database'])
                    p = BatchProcess(
                        desc=BackupMessage(
                            BACKUP.OBJECT, server.id, bfile,
                            *args,
                            database=job.data['database']
                        ),
                        cmd=utility, args=escaped_args, manager_obj=manager
                    )
                else:
                    p = BatchProcess(
                        desc=BackupMessage(
                            BACKUP.SERVER if backup_obj_type != 'globals' else BACKUP.GLOBALS,
                            server.id, bfile,
                            *args
                        ),
                        cmd=utility, args=escaped_args, manager_obj=manager
                    )
                
                # Set environment variables and start process
                p.set_env_variables(server)
                p.start()
                
                # Wait for process to complete
                while p.status == 'running':
                    time.sleep(1)
                
                if p.status == 'completed':
                    job.last_status = 'success'
                    self.logger.info(f"Backup process completed successfully: job_id={p.id}")
                else:
                    job.last_status = 'failed'
                    self.logger.error(f"Backup process failed with status: {p.status}")
                
        except Exception as e:
            self.logger.error(f"Backup execution failed: {e}")
            self.logger.error(traceback.format_exc())
            job.last_status = 'failed'
            raise

# Initialize the scheduler
backup_scheduler = BackupScheduler()

def create_module(app, **kwargs):
    """
    Initialize the module
    """
    try:
        print("\n=== Starting Backup Module Initialization ===")
        
        # Configure scheduler with app
        print("Step 1: Initializing backup scheduler...")
        backup_scheduler.init_app(app)
        
        # Explicitly start the scheduler in the application context
        with app.app_context():
            print("Step 2: Starting backup scheduler...")
            try:
                if not backup_scheduler.running:
                    success = backup_scheduler.start()
                    if success:
                        print("Scheduler started successfully")
                    else:
                        print("Failed to start scheduler")
                else:
                    print("Scheduler was already running")
            except Exception as e:
                print(f"ERROR: Failed to start scheduler: {e}")
                import traceback
                traceback.print_exc()
        
        # Additional logging and verification
        print("Step 3: Checking scheduler status...")
        status = {
            'running': backup_scheduler.running,
            'initialized': backup_scheduler.initialized,
            'thread_alive': backup_scheduler.thread.is_alive() if backup_scheduler.thread else False,
            'job_count': sum(len(jobs) for jobs in backup_scheduler.jobs.values())
        }
        print(f"Scheduler Status: {status}")
        
        # Add a route to check scheduler status
        @app.route('/backup/scheduler/status')
        def check_scheduler_status():
            return make_json_response(data=status)
        
        print("=== Backup Module Initialization Complete ===\n")
        
        return blueprint
        
    except Exception as e:
        print(f"\nERROR: Failed to initialize backup scheduler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if app and hasattr(app, 'logger'):
            app.logger.error(f"Failed to initialize backup scheduler: {str(e)}")
            app.logger.error(traceback.format_exc())
        
        raise

@blueprint.route('/scheduler_status', methods=['GET'])
@pga_login_required
def scheduler_status():
    """Return status of the backup scheduler"""
    status_data = {
        'running': backup_scheduler.running,
        'initialized': backup_scheduler.initialized,
        'job_count': sum(len(jobs) for jobs in backup_scheduler.jobs.values()),
        'last_check': backup_scheduler.last_check_time.isoformat() if backup_scheduler.last_check_time else None,
        'jobs': {},
        'recent_logs': backup_scheduler.status_log[-10:] if backup_scheduler.status_log else []
    }
    
    # Include job details
    for sid, job_list in backup_scheduler.jobs.items():
        status_data['jobs'][str(sid)] = []
        for job in job_list:
            job_info = {
                'type': job.schedule_type,
                'last_run': job.last_run.isoformat() if job.last_run else None,
                'next_run': job.next_run.isoformat() if job.next_run else None,
                'run_count': job.run_count,
                'last_status': job.last_status,
                'backup_type': job.data.get('type', 'unknown'),
                'file': job.data.get('file', 'unknown'),
            }
            status_data['jobs'][str(sid)].append(job_info)
    
    return make_json_response(data=status_data)

@blueprint.route('/restart_scheduler', methods=['POST'])
@pga_login_required
def restart_scheduler():
    """Restart the backup scheduler"""
    try:
        if backup_scheduler.running:
            backup_scheduler.stop()
        backup_scheduler.start()
        return make_json_response(
            data={'message': 'Scheduler restarted successfully', 'Success': 1}
        )
    except Exception as e:
        return make_json_response(
            success=0,
            errormsg=f'Failed to restart scheduler: {str(e)}'
        )

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
    print(f"DEBUG: create_backup_objects_job called with sid={sid}, scheduled_data={scheduled_data is not None}")
    
    try:
        data = scheduled_data if scheduled_data else json.loads(request.data)
        backup_obj_type = data.get('type', 'objects')
        
        print(f"DEBUG: Backup job details: type={backup_obj_type}, file={data.get('file', 'Not specified')}")

        # Handle scheduler if enabled
        if not scheduled_data and data.get('enable_scheduler'):
            try:
                schedule_type = data.get('schedule_type')
                start_date_time = data.get('start_date_time')
                print(f"DEBUG: Scheduling backup: type={schedule_type}, start_time={start_date_time}")
                
                # start_date_time = "2025-03-25 01:26:00"
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
                    
                    # Check if scheduler is running
                    if not backup_scheduler.running:
                        print("DEBUG: Warning - Scheduler is not running, but will still add the job")
                        
                    # Add job to scheduler with backup configuration
                    print(f"DEBUG: Adding job to scheduler: scheduler_running={backup_scheduler.running}")
                    backup_scheduler.add_job(
                        sid=sid,
                        data=backup_config,
                        schedule_type=schedule_type,
                        start_time=start_datetime
                    )
                    
                    print(f"DEBUG: Job scheduled successfully for {start_datetime}")
                    
                    return make_json_response(
                        data={
                            'message': 'Backup scheduled successfully', 
                            'Success': 1,
                            'schedule_info': {
                                'type': schedule_type,
                                'start_time': start_datetime.isoformat(),
                                'server_id': sid
                            }
                        }
                    )
                except ValueError as e:
                    print(f"DEBUG ERROR: Invalid datetime format: {str(e)}")
                    return make_json_response(
                        success=0,
                        errormsg=f'Invalid datetime format: {str(e)}'
                    )
            except Exception as e:
                print(f"DEBUG ERROR: Error scheduling backup: {str(e)}")
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
            
            # Log execution for scheduled backups
            if scheduled_data:
                current_app.logger.info(f"Scheduled backup started: job_id={p.id}, server={server.id}, file={data['file']}")
            
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
