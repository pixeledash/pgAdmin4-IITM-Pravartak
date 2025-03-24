/////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2025, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////
import gettext from 'sources/gettext';
import BaseUISchema from 'sources/SchemaView/base_schema.ui';
import { isEmptyString } from 'sources/validators';

export class SectionSchema extends BaseUISchema {
  constructor(fieldOptions={}, initValues={}) {
    super({
      ...initValues,
    });

    this.fieldOptions = {
      ...fieldOptions,
    };
  }

  get idAttribute() {
    return 'id';
  }


  get baseFields() {
    return [
      {
        id: 'pre_data',
        label: gettext('Pre-data'),
        type: 'switch',
        group: gettext('Sections'),
        deps: ['only_data', 'only_schema', 'only_tablespaces', 'only_roles'],
        disabled: function(state) {
          return state.only_data ||
           state.only_schema ||
           state.only_tablespaces ||
           state.only_roles;
        },
        inlineGroup: 'section',
      }, {
        id: 'data',
        label: gettext('Data'),
        type: 'switch',
        group: gettext('Sections'),
        deps: ['only_data', 'only_schema', 'only_tablespaces', 'only_roles'],
        disabled: function(state) {
          return state.only_data ||
           state.only_schema ||
           state.only_tablespaces ||
           state.only_roles;
        },
        inlineGroup: 'section',
      }, {
        id: 'post_data',
        label: gettext('Post-data'),
        type: 'switch',
        group: gettext('Sections'),
        deps: ['only_data', 'only_schema', 'only_tablespaces', 'only_roles'],
        disabled: function(state) {
          return state.only_data ||
           state.only_schema ||
           state.only_tablespaces ||
           state.only_roles;
        },
        inlineGroup: 'section',
      }
    ];
  }
}

export function getSectionSchema() {
  return new SectionSchema();
}

export class TypeObjSchema extends BaseUISchema {
  constructor(fieldOptions={}) {
    super();

    this.fieldOptions = {
      ...fieldOptions,
    };
  }

  get idAttribute() {
    return 'id';
  }


  get baseFields() {
    let obj = this;
    return [{
      id: 'only_data',
      label: gettext('Only data'),
      type: 'switch',
      group: gettext('Type of objects'),
      deps: ['pre_data', 'data', 'post_data', 'only_schema',
        'only_tablespaces', 'only_roles'],
      disabled: function(state) {
        return state.pre_data ||
           state.data ||
           state.post_data ||
           state.only_schema ||
           state.only_tablespaces ||
           state.only_roles;
      },
      inlineGroup: 'type_of_objects',
    }, {
      id: 'only_schema',
      label: gettext('Only schemas'),
      type: 'switch',
      group: gettext('Type of objects'),
      deps: ['pre_data', 'data', 'post_data', 'only_data',
        'only_tablespaces', 'only_roles'],
      disabled: function(state) {
        return state.pre_data ||
           state.data ||
           state.post_data ||
           state.only_data ||
           state.only_tablespaces ||
           state.only_roles;
      },
      inlineGroup: 'type_of_objects',
    },  {
      id: 'only_tablespaces',
      label: gettext('Only tablespaces'),
      type: 'switch',
      group: gettext('Type of objects'),
      deps: ['pre_data', 'data', 'post_data', 'only_data', 'only_schema',
        'only_roles'],
      disabled: function(state) {
        return state.pre_data ||
           state.data ||
           state.post_data ||
           state.only_data ||
           state.only_schema ||
           state.only_roles;
      },
      visible: isVisibleForObjectBackup(obj?.top?.backupType),
      inlineGroup: 'type_of_objects',
    }, {
      id: 'only_roles',
      label: gettext('Only roles'),
      type: 'switch',
      group: gettext('Type of objects'),
      deps: ['pre_data', 'data', 'post_data', 'only_data', 'only_schema',
        'only_tablespaces'],
      inlineGroup: 'type_of_objects',
      disabled: function(state) {
        return state.pre_data ||
           state.data ||
           state.post_data ||
           state.only_data ||
           state.only_schema ||
           state.only_tablespaces;
      },
      visible: isVisibleForObjectBackup(obj?.top?.backupType)
    }, {
      id: 'blobs',
      label: gettext('Blobs'),
      type: 'switch',
      group: gettext('Type of objects'),
      inlineGroup: 'type_of_objects',
      visible: function(state) {
        if (!isVisibleForServerBackup(obj?.top?.backupType)) {
          state.blobs = false;
          return false;
        }
        return true;
      },
    }];
  }
}

export function getTypeObjSchema(fieldOptions) {
  return new TypeObjSchema(fieldOptions);
}

export class SaveOptSchema extends BaseUISchema {
  constructor(fieldOptions={}, initValues={}) {
    super({
      id: null,
      ...initValues,
    });

    this.fieldOptions = {
      nodeInfo: null,
      ...fieldOptions,
    };
  }

  get idAttribute() {
    return 'id';
  }

  get baseFields() {
    let obj = this;
    return [{
      id: 'dns_owner',
      label: gettext('Owner'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
    }, {
      id: 'dns_no_role_passwords',
      label: gettext('Role passwords'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      visible: isVisibleForObjectBackup(obj?.top?.backupType),
      inlineGroup: 'do_not_save',
    }, {
      id: 'dns_privilege',
      label: gettext('Privileges'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
    }, {
      id: 'dns_tablespace',
      label: gettext('Tablespaces'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
    }, {
      id: 'dns_unlogged_tbl_data',
      label: gettext('Unlogged table data'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
    }, {
      id: 'dns_comments',
      label: gettext('Comments'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
      min_version: 110000
    }, {
      id: 'dns_publications',
      label: gettext('Publications'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
      min_version: 110000
    }, {
      id: 'dns_subscriptions',
      label: gettext('Subscriptions'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
      min_version: 110000
    }, {
      id: 'dns_security_labels',
      label: gettext('Security labels'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
      min_version: 110000
    }, {
      id: 'dns_toast_compression',
      label: gettext('Toast compressions'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
      min_version: 140000
    }, {
      id: 'dns_table_access_method',
      label: gettext('Table access methods'),
      type: 'switch',
      disabled: false,
      group: gettext('Do not save'),
      inlineGroup: 'do_not_save',
      min_version: 150000
    }];
  }
}

export function getSaveOptSchema(fieldOptions) {
  return new SaveOptSchema(fieldOptions);
}

function isVisibleForServerBackup(backupType) {
  return !(!_.isUndefined(backupType) && backupType === 'server');
}

function isVisibleForObjectBackup(backupType) {
  return !(!_.isUndefined(backupType) && backupType === 'backup_objects');
}

export class DisabledOptionSchema extends BaseUISchema {
  constructor(fieldOptions={}, initValues={}) {
    super({
      id: null,
      ...initValues,
    });

    this.fieldOptions = {
      nodeInfo: null,
      ...fieldOptions,
    };
  }

  get idAttribute() {
    return 'id';
  }


  get baseFields() {
    return [{
      id: 'disable_trigger',
      label: gettext('Triggers'),
      type: 'switch',
      group: gettext('Disable'),
      deps: ['only_data'],
      disabled: function(state) {
        return !(state.only_data);
      },
      inlineGroup: 'disable',
    }, {
      id: 'disable_quoting',
      label: gettext('$ quoting'),
      type: 'switch',
      disabled: false,
      group: gettext('Disable'),
      inlineGroup: 'disable',
    }];
  }
}

export function getDisabledOptionSchema(fieldOptions) {
  return new DisabledOptionSchema(fieldOptions);
}

export class MiscellaneousSchema extends BaseUISchema {
  constructor(fieldOptions={}, initValues={}) {
    super({
      id: null,
      verbose: true,
      ...initValues,
    });

    this.fieldOptions = {
      nodeInfo: null,
      ...fieldOptions,
    };
  }

  get idAttribute() {
    return 'id';
  }


  get baseFields() {
    let obj = this;
    return [{
      id: 'verbose',
      label: gettext('Verbose messages'),
      type: 'switch',
      disabled: false,
      group: gettext('Miscellaneous'),
      inlineGroup: 'miscellaneous',
    }, {
      id: 'dqoute',
      label: gettext('Force double quote on identifiers'),
      type: 'switch',
      disabled: false,
      group: gettext('Miscellaneous'),
      inlineGroup: 'miscellaneous',
    }, {
      id: 'use_set_session_auth',
      label: gettext('Use SET SESSION AUTHORIZATION'),
      type: 'switch',
      disabled: false,
      group: gettext('Miscellaneous'),
      inlineGroup: 'miscellaneous',
    }, {
      id: 'exclude_schema',
      label: gettext('Exclude schema'),
      type: 'select',
      disabled: false,
      group: gettext('Miscellaneous'),
      inlineGroup: 'miscellaneous',
      visible: isVisibleForServerBackup(obj?.top?.backupType),
      controlProps: { multiple: true, allowClear: false, creatable: true, noDropdown: true, placeholder: ' ' }
    }, {
      id: 'exclude_database',
      label: gettext('Exclude database'),
      type: 'select',
      disabled: false,
      min_version: 160000,
      group: gettext('Miscellaneous'),
      visible: isVisibleForObjectBackup(obj?.top?.backupType),
      controlProps: { multiple: true, allowClear: false, creatable: true, noDropdown: true, placeholder: ' ' }
    }, {
      id: 'extra_float_digits',
      label: gettext('Extra float digits'),
      type: 'int',
      disabled: false,
      group: gettext('Miscellaneous'),
      min_version: 120000
    }, {
      id: 'lock_wait_timeout',
      label: gettext('Lock wait timeout'),
      type: 'int',
      disabled: false,
      group: gettext('Miscellaneous')
    }];
  }
}

export function getMiscellaneousSchema(fieldOptions) {
  return new MiscellaneousSchema(fieldOptions);
}

export class ExcludePatternsSchema extends BaseUISchema {
  constructor(fieldOptions={}, initValues={}) {
    super({
      ...initValues,
    });

    this.fieldOptions = {
      ...fieldOptions,
    };
  }

  get idAttribute() {
    return 'id';
  }

  get baseFields() {
    let obj = this;
    return [{
      id: 'exclude_table',
      label: gettext('Table(s)'),
      type: 'select',
      disabled: false,
      group: gettext('Table Options'),
      visible: isVisibleForServerBackup(obj?.top?.backupType),
      controlProps: { multiple: true, allowClear: false, creatable: true, noDropdown: true, placeholder: ' ' }
    }, {
      id: 'exclude_table_data',
      label: gettext('Table(s) data'),
      type: 'select',
      disabled: false,
      group: gettext('Table Options'),
      visible: isVisibleForServerBackup(obj?.top?.backupType),
      controlProps: { multiple: true, allowClear: false, creatable: true, noDropdown: true, placeholder: ' ' }
    }, {
      id: 'exclude_table_and_children',
      label: gettext('Table(s) and children'),
      type: 'select',
      disabled: false,
      group: gettext('Table Options'),
      min_version: 160000,
      visible: isVisibleForServerBackup(obj?.top?.backupType),
      controlProps: { multiple: true, allowClear: false, creatable: true, noDropdown: true, placeholder: ' ' }
    }, {
      id: 'exclude_table_data_and_children',
      label: gettext('Table(s) data and children'),
      type: 'select',
      disabled: false,
      group: gettext('Table Options'),
      min_version: 160000,
      visible: isVisibleForServerBackup(obj?.top?.backupType),
      controlProps: { multiple: true, allowClear: false, creatable: true, noDropdown: true, placeholder: ' ' }
    }];
  }
}

export function getExcludePatternsSchema() {
  return new ExcludePatternsSchema();
}

export class SchedulerSchema extends BaseUISchema {
  constructor(fieldOptions={}, initValues={}) {
    super({
      enable_scheduler: false,
      schedule_type: 'one_time',
      start_date_time: null,
      ...initValues,
    });

    this.fieldOptions = {
      ...fieldOptions,
    };
  }

  get idAttribute() {
    return 'id';
  }

  get baseFields() {
    return [{
      id: 'enable_scheduler',
      label: gettext('Enable scheduler'),
      type: 'switch',
      group: gettext('Scheduler'),
      disabled: false,
    }, {
      id: 'schedule_type',
      label: gettext('Schedule type'),
      type: 'select',
      options: [
        {label: gettext('One time'), value: 'one_time'},
        {label: gettext('Daily'), value: 'daily'},
        {label: gettext('Weekly'), value: 'weekly'},
        {label: gettext('Monthly'), value: 'monthly'}
      ],
      controlProps: {
        allowClear: false,
        width: '100%'
      },
      deps: ['enable_scheduler'],
      disabled: (state) => !state.enable_scheduler,
      group: gettext('Scheduler'),
    }, {
      id: 'start_date_time',
      label: gettext('Start date and time'),
      type: 'datetimepicker',
      controlProps: {
        autoOk: true,
        disablePast: true,
        placeholder: gettext('YYYY-MM-DD HH:mm:ss'),
        showSeconds: true,
        ampm: false,
      },
      deps: ['enable_scheduler'],
      disabled: (state) => !state.enable_scheduler,
      group: gettext('Scheduler'),
    }, {
      id: 'repeat_days',
      label: gettext('Repeat days'),
      type: 'select',
      options: [
        {label: gettext('Monday'), value: 'monday'},
        {label: gettext('Tuesday'), value: 'tuesday'},
        {label: gettext('Wednesday'), value: 'wednesday'},
        {label: gettext('Thursday'), value: 'thursday'},
        {label: gettext('Friday'), value: 'friday'},
        {label: gettext('Saturday'), value: 'saturday'},
        {label: gettext('Sunday'), value: 'sunday'}
      ],
      controlProps: {
        multiple: true,
        allowClear: false,
        width: '100%'
      },
      deps: ['enable_scheduler', 'schedule_type'],
      disabled: (state) => !state.enable_scheduler || state.schedule_type !== 'weekly',
      group: gettext('Scheduler'),
    }, {
      id: 'repeat_months',
      label: gettext('Repeat months'),
      type: 'select',
      options: [
        {label: gettext('January'), value: '1'},
        {label: gettext('February'), value: '2'},
        {label: gettext('March'), value: '3'},
        {label: gettext('April'), value: '4'},
        {label: gettext('May'), value: '5'},
        {label: gettext('June'), value: '6'},
        {label: gettext('July'), value: '7'},
        {label: gettext('August'), value: '8'},
        {label: gettext('September'), value: '9'},
        {label: gettext('October'), value: '10'},
        {label: gettext('November'), value: '11'},
        {label: gettext('December'), value: '12'}
      ],
      controlProps: {
        multiple: true,
        allowClear: false,
        width: '100%'
      },
      deps: ['enable_scheduler', 'schedule_type'],
      disabled: (state) => !state.enable_scheduler || state.schedule_type !== 'monthly',
      group: gettext('Scheduler'),
    }];
  }

  validate(state, setError) {
    if (state.enable_scheduler) {
      if (!state.start_date_time) {
        setError('start_date_time', gettext('Start date and time cannot be empty'));
        return true;
      }
    }
    return false;
  }
}

export function getSchedulerSchema() {
  return new SchedulerSchema();
}

export default class BackupSchema extends BaseUISchema {
  constructor(sectionSchema, typeObjSchema, saveOptSchema, disabledOptionSchema, miscellaneousSchema, excludePatternsSchema, schedulerSchema, fieldOptions = {}, treeNodeInfo=[], pgBrowser=null, backupType='server', objects={}) {
    super({
      file: undefined,
      format: 'custom',
      id: null,
      blobs: true,
      verbose: true,
      enable_scheduler: false,
    });

    this.fieldOptions = {
      encoding: null,
      role: null,
      ...fieldOptions,
    };
    this.treeData = objects?.objects;
    this.treeNodeInfo = treeNodeInfo;
    this.pgBrowser = pgBrowser;
    this.backupType = backupType;
    this.getSectionSchema = sectionSchema;
    this.getTypeObjSchema = typeObjSchema;
    this.getSaveOptSchema = saveOptSchema;
    this.getDisabledOptionSchema = disabledOptionSchema;
    this.getMiscellaneousSchema = miscellaneousSchema;
    this.getExcludePatternsSchema = excludePatternsSchema;
    this.getSchedulerSchema = schedulerSchema;
  }

  get idAttribute() {
    return 'id';
  }

  get baseFields() {
    let obj = this;
    return [{
      id: 'file',
      label: gettext('Filename'),
      type: 'file',
      disabled: false,
      controlProps: {
        dialogType: 'create_file',
        supportedTypes: ['*', 'sql', 'backup'],
        dialogTitle: 'Select file',
      },
      deps: ['format'],
    }, {
      id: 'format',
      label: gettext('Format'),
      type: 'select',
      disabled: false,
      controlProps: { allowClear: false, width: '100%' },
      options: [
        {
          label: gettext('Custom'),
          value: 'custom',
        },
        {
          label: gettext('Tar'),
          value: 'tar',
        },
        {
          label: gettext('Plain'),
          value: 'plain',
        },
        {
          label: gettext('Directory'),
          value: 'directory',
        },
      ],
      visible: function(state) {
        if (!isVisibleForServerBackup(obj.backupType)) {
          state.format = 'plain';
          return false;
        }
        return true;
      },
    }, {
      id: 'ratio',
      label: gettext('Compression ratio'),
      type: 'int',
      min: 0,
      max: 9,
      deps: ['format'],
      disabled: function(state) {
        return (state.format === 'tar');
      },
      visible: isVisibleForServerBackup(obj.backupType),
    }, {
      id: 'encoding',
      label: gettext('Encoding'),
      type: 'select',
      disabled: false,
      options: obj.fieldOptions.encoding,
      min_version: 110000,
      visible: isVisibleForServerBackup(obj.backupType)
    }, {
      id: 'no_of_jobs',
      label: gettext('Number of jobs'),
      type: 'int',
      deps: ['format'],
      disabled: function(state) {
        return (state.format !== 'directory');
      },
      visible: isVisibleForServerBackup(obj.backupType),
    }, {
      id: 'role',
      label: gettext('Role name'),
      type: 'select',
      options: obj.fieldOptions.role,
      controlProps: {
        allowClear: false,
      },
    }, {
      id: 'server_note',
      label: gettext('Note'),
      text: gettext('The backup format will be PLAIN'),
      type: 'note',
      visible: function() {
        return obj.backupType === 'server';
      },
    }, {
      type: 'nested-fieldset',
      label: gettext('Sections'),
      group: gettext('Data Options'),
      schema:new getSectionSchema(),
      visible: isVisibleForServerBackup(obj.backupType)
    }, {
      type: 'nested-fieldset',
      label: gettext('Type of objects'),
      group: gettext('Data Options'),
      schema: obj.getTypeObjSchema()
    }, {
      type: 'nested-fieldset',
      label: gettext('Do not save'),
      group: gettext('Data Options'),
      schema: obj.getSaveOptSchema(),
    }, {
      id: 'use_insert_commands',
      label: gettext('Use INSERT Commands'),
      type: 'switch',
      disabled: false,
      group: gettext('Query Options'),
    }, {
      id: 'max_rows_per_insert',
      label: gettext('Maximum rows per INSERT command'),
      type: 'int', min: 1,
      disabled: false,
      group: gettext('Query Options'),
      min_version: 120000
    }, {
      id: 'on_conflict_do_nothing',
      label: gettext('On conflict do nothing to INSERT command'),
      type: 'switch',
      group: gettext('Query Options'),
      min_version: 120000,
      deps: ['use_insert_commands', 'rows_per_insert', 'use_column_inserts'],
      disabled: function(state) {
        if (state.use_insert_commands || state.use_column_inserts || state.rows_per_insert > 0) {
          return false;
        }
        state.on_conflict_do_nothing = false;
        return true;
      },
      inlineGroup: 'miscellaneous',
    }, {
      id: 'include_create_database',
      label: gettext('Include CREATE DATABASE statement'),
      type: 'switch',
      disabled: false,
      group: gettext('Query Options'),
      visible: isVisibleForServerBackup(obj.backupType),
      inlineGroup: 'miscellaneous',
    }, {
      id: 'include_drop_database',
      label: gettext('Include DROP DATABASE statement'),
      type: 'switch',
      group: gettext('Query Options'),
      deps: ['only_data'],
      disabled: function(state) {
        if (state.only_data) {
          state.include_drop_database = false;
          return true;
        }
        return false;
      },
      inlineGroup: 'miscellaneous',
    }, {
      id: 'if_exists',
      label: gettext('Include IF EXISTS clause'),
      type: 'switch',
      group: gettext('Query Options'),
      deps: ['only_data, include_drop_database'],
      disabled: function(state) {
        if (state.include_drop_database) {
          return false;
        }
        state.if_exists = false;
        return true;
      },
      inlineGroup: 'miscellaneous',
    }, {
      id: 'use_column_inserts',
      label: gettext('Use Column INSERTS'),
      type: 'switch',
      disabled: false,
      group: gettext('Table Options'),
    }, {
      id: 'load_via_partition_root',
      label: gettext('Load via partition root'),
      type: 'switch',
      disabled: false,
      group: gettext('Table Options'),
      min_version: 110000
    }, {
      id: 'enable_row_security',
      label: gettext('Enable row security'),
      type: 'switch',
      group: gettext('Table Options'),
      deps:['use_insert_commands'],
      disabled: function(state) {
        if (state.use_insert_commands) {
          return false;
        }
        state.enable_row_security = false;
        return true;
      },
      visible: isVisibleForServerBackup(obj.backupType),
      helpMessage: gettext('This option is enabled only when Use INSERT Commands is enabled.')
    }, {
      id: 'table_and_children',
      label: gettext('Include table(s) and Children'),
      type: 'select',
      disabled: false,
      group: gettext('Table Options'),
      min_version: 160000,
      visible: isVisibleForServerBackup(obj.backupType),
      controlProps: { multiple: true, allowClear: false, creatable: true, noDropdown: true, placeholder: ' ' }
    }, {
      type: 'nested-fieldset',
      label: gettext('Exclude patterns'),
      group: gettext('Table Options'),
      schema: obj.getExcludePatternsSchema(),
      visible: isVisibleForServerBackup(obj.backupType),
    }, {
      type: 'nested-fieldset',
      label: gettext('Disable'),
      group: gettext('Options'),
      schema: obj.getDisabledOptionSchema(),
    }, {
      type: 'nested-fieldset',
      label: gettext('Miscellaneous'),
      group: gettext('Options'),
      schema: obj.getMiscellaneousSchema(),
    }, {
      id: 'object',
      label: gettext('Objects'),
      type: 'group',
      visible: isVisibleForServerBackup(obj?.backupType)
    }, {
      id: 'objects',
      label: gettext('objects'),
      group: gettext('Objects'),
      type: 'tree',
      helpMessage: gettext('If Schema(s) is selected then it will take the backup of that selected schema(s) only'),
      treeData: this.treeData,
      visible: () => {
        return isVisibleForServerBackup(obj?.backupType);
      },
      depChange: (state)=> {
        let selectedNodeCollection = {
          'schema': [],
          'table': [],
          'view': [],
          'sequence': [],
          'foreign table': [],
          'materialized view': [],
        };
        state?.objects?.forEach((node)=> {
          if(node.data.is_schema && !node.data?.isIndeterminate) {
            selectedNodeCollection['schema'].push(node.data.name);
          } else if(['table', 'view', 'materialized view', 'foreign table', 'sequence'].includes(node.data.type) &&
              !node.data.is_collection && !selectedNodeCollection['schema'].includes(node.data.schema)) {
            selectedNodeCollection[node.data.type].push(node.data);
          }
        });
        return {'objects': selectedNodeCollection};
      },
      hasCheckbox: true,
      isFullTab: true,
    }, {
      type: 'nested-fieldset',
      label: gettext('Scheduler'),
      group: gettext('Scheduler'),
      schema: obj.getSchedulerSchema(),
      isTabPanel: true,
    }];
  }

  validate(state, setError) {
    if (isEmptyString(state.service)) {
      let errmsg = null;
      /* events validation*/
      if (!state.file) {
        errmsg = gettext('Please provide a filename.');
        setError('file', errmsg);
        return true;
      } else {
        setError('file', null);
      }
    }
  }
}
