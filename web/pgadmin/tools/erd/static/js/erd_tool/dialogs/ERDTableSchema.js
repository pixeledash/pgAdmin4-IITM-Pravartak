import TableSchema from '../../../../../../browser/server_groups/servers/databases/schemas/tables/static/js/table.ui';

class ERDTableSchema extends TableSchema {
  constructor(fieldOptions={}, nodeInfo={}, schemas={}, getPrivilegeRoleSchema=()=>{/*This is intentional (SonarQube)*/}, getColumns=()=>[],
    getCollations=()=>[], getOperatorClass=()=>[], getAttachTables=()=>[], initValues={}, inErd=false) {
    super(fieldOptions, nodeInfo, schemas, getPrivilegeRoleSchema, getColumns,
      getCollations, getOperatorClass, getAttachTables, initValues, inErd);
  }

  generateSQL(state) {
    if (!state.name || !state.schema) {
      return '';
    }

    let sql = `CREATE TABLE ${state.schema}.${state.name} (\n`;

    // Add columns
    if (state.columns && state.columns.length > 0) {
      const columnDefs = state.columns.map(col => {
        let def = `  ${col.name} ${col.cltype}`;
        if (col.colconstraint) {
          def += ` ${col.colconstraint}`;
        }
        return def;
      });
      sql += columnDefs.join(',\n');
    }

    // Add constraints
    if (state.constraints && state.constraints.length > 0) {
      if (state.columns && state.columns.length > 0) {
        sql += ',\n';
      }
      const constraintDefs = state.constraints.map(cons => {
        let def = `  ${cons.conname} `;
        if (cons.contype === 'p') {
          def += `PRIMARY KEY (${cons.columns.join(', ')})`;
        } else if (cons.contype === 'f') {
          def += `FOREIGN KEY (${cons.columns.join(', ')}) REFERENCES ${cons.references}`;
        }
        return def;
      });
      sql += constraintDefs.join(',\n');
    }

    sql += '\n);';
    return sql;
  }

  get baseFields() {
    const fields = super.baseFields;
    fields.push({
      id: 'sql_preview',
      label: 'SQL Preview',
      type: 'text',
      mode: ['create'],
      group: 'SQL',
      visible: true,
      readonly: true,
      deps: ['schema', 'name', 'columns', 'constraints'],
      depChange: (state, _source, _topState, _topSource) => {
        return this.generateSQL(state);
      }
    });
    return fields;
  }
}

export default ERDTableSchema; 