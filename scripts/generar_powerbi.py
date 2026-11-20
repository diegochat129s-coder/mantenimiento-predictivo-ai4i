"""Construye un proyecto Power BI con conexión de importación a SQL Server."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def column(name, data_type='int64', **properties):
    return {'name': name, 'dataType': data_type, 'sourceColumn': name,
            'summarizeBy': 'none', **properties}


def table(name, columns):
    return {
        'name': name, 'columns': columns,
        'partitions': [{'name': name, 'mode': 'import', 'source': {
            'type': 'm', 'expression': [
                'let',
                '    Origen = Sql.Database(ServidorSQL, BaseDatosSQL, [CreateNavigationProperties=false]),',
                f'    Tabla = Origen{{[Schema="dm",Item="{name}"]}}[Data]',
                'in', '    Tabla',
            ]}}],
    }


def field(entity, name, measure=False):
    return {('Measure' if measure else 'Column'): {
        'Expression': {'SourceRef': {'Entity': entity}}, 'Property': name}}


def projection(entity, name, measure=False):
    return {'field': field(entity, name, measure), 'queryRef': f'{entity}.{name}', 'nativeQueryRef': name}


def visual(name, kind, x, y, width, height, roles, title):
    return {
        '$schema': BASE_SCHEMA + 'item/report/definition/visualContainer/2.4.0/schema.json',
        'name': name,
        'position': {'x': x, 'y': y, 'z': 0, 'width': width, 'height': height, 'tabOrder': 0},
        'visual': {
            'visualType': kind,
            'query': {'queryState': {role: {'projections': values} for role, values in roles.items()}},
            'visualContainerObjects': {'title': [{'properties': {
                'show': {'expr': {'Literal': {'Value': 'true'}}},
                'text': {'expr': {'Literal': {'Value': "'" + title.replace("'", "''") + "'"}}},
            }}]},
            'drillFilterOtherVisuals': True,
        },
    }


def generate(server, database, root=ROOT):
    output = root / 'powerbi'
    model_folder = output / 'Mantenimiento.SemanticModel'
    report_folder = output / 'Mantenimiento.Report'
    fact_columns = [column('udi'), column('product_id', 'string'), column('tipo_id'),
                    column('estado_id'), column('tiempo_id')]
    fact_columns += [column(x, 'double') for x in ['air_temperature_k', 'process_temperature_k', 'torque_nm']]
    fact_columns += [column(x) for x in ['rotational_speed_rpm', 'tool_wear_min']]
    fact_columns += [column(x, 'boolean') for x in ['twf', 'hdf', 'pwf', 'osf', 'rnf']]
    fact_columns += [column('fecha_carga_utc', 'dateTime'), column('carga_id', 'string')]
    fact = table('fact_operacion', fact_columns)
    measures = [
        ('Observaciones', 'COUNTROWS(fact_operacion)', '#,0'),
        ('Fallas', 'SUM(fact_operacion[estado_id])', '#,0'),
        ('Porcentaje de fallas', 'DIVIDE([Fallas], [Observaciones], 0)', '0.00%'),
        ('Torque promedio', 'AVERAGE(fact_operacion[torque_nm])', '0.00 "Nm"'),
        ('Desgaste promedio', 'AVERAGE(fact_operacion[tool_wear_min])', '0.00 "min"'),
        ('Temperatura promedio', 'AVERAGE(fact_operacion[process_temperature_k])', '0.00 "K"'),
    ]
    fact['measures'] = [{'name': name, 'expression': expression, 'formatString': fmt} for name, expression, fmt in measures]
    time_columns = [column('tiempo_id'), column('fecha', 'dateTime', isKey=True, formatString='dd/MM/yyyy'),
                    column('anio'), column('trimestre'), column('mes'),
                    column('mes_nombre', 'string', sortByColumn='mes'), column('anio_mes', 'string'),
                    column('dia'), column('dia_semana'),
                    column('dia_nombre', 'string', sortByColumn='dia_semana'),
                    column('es_fin_semana', 'boolean'), column('es_fecha_simulada', 'boolean')]
    time = table('dim_tiempo', time_columns)
    time['dataCategory'] = 'Time'
    time['description'] = 'Calendario 2026. Fechas de operación simuladas: 50 observaciones por día desde el 1 de enero.'
    model = {'name': 'MantenimientoPredictivo', 'compatibilityLevel': 1600, 'model': {
        'culture': 'es-MX', 'defaultPowerBIDataSourceVersion': 'powerBI_V3',
        'sourceQueryCulture': 'es-MX',
        'expressions': [
            {'name': 'ServidorSQL', 'kind': 'm', 'expression': '"' + server.replace('"', '""') + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'},
            {'name': 'BaseDatosSQL', 'kind': 'm', 'expression': '"' + database.replace('"', '""') + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'},
        ],
        'tables': [fact, table('dim_tipo', [column('tipo_id'), column('tipo', 'string'), column('calidad', 'string')]),
                   table('dim_estado', [column('estado_id'), column('descripcion', 'string')]), time],
        'relationships': [
            {'name': 'operacion_' + name, 'fromTable': 'fact_operacion', 'fromColumn': name + '_id',
             'toTable': 'dim_' + name, 'toColumn': name + '_id', 'fromCardinality': 'many',
             'toCardinality': 'one', 'crossFilteringBehavior': 'oneDirection', 'isActive': True}
            for name in ['tipo', 'estado', 'tiempo']],
    }}
    write_json(model_folder / 'model.bim', model)
    write_json(model_folder / 'definition.pbism', {
        '$schema': BASE_SCHEMA + 'item/semanticModel/definitionProperties/1.0.0/schema.json',
        'version': '1.0', 'settings': {}})
    write_json(output / 'Mantenimiento.pbip', {
        '$schema': BASE_SCHEMA + 'pbip/pbipProperties/1.0.0/schema.json',
        'version': '1.0', 'artifacts': [{'report': {'path': 'Mantenimiento.Report'}}],
        'settings': {'enableAutoRecovery': True},
    })
    write_json(report_folder / 'definition.pbir', {
        '$schema': BASE_SCHEMA + 'item/report/definitionProperties/2.0.0/schema.json',
        'version': '4.0', 'datasetReference': {'byPath': {'path': '../Mantenimiento.SemanticModel'}},
    })
    definition = report_folder / 'definition'
    write_json(definition / 'report.json', {
        '$schema': BASE_SCHEMA + 'item/report/definition/report/2.0.0/schema.json',
        'themeCollection': {'baseTheme': {'name': 'CY24SU06', 'reportVersionAtImport': '5.55', 'type': 'SharedResources'}},
    })
    page = definition / 'pages/operacion'
    write_json(definition / 'pages/pages.json', {
        '$schema': BASE_SCHEMA + 'item/report/definition/pagesMetadata/1.0.0/schema.json',
        'pageOrder': ['operacion'], 'activePageName': 'operacion',
    })
    write_json(page / 'page.json', {
        '$schema': BASE_SCHEMA + 'item/report/definition/page/2.0.0/schema.json',
        'name': 'operacion', 'displayName': 'Operación · fechas simuladas',
        'displayOption': 'FitToPage', 'height': 720, 'width': 1280,
    })
    visuals = []
    for i, (measure, _, _) in enumerate(measures[:4]):
        visuals.append(visual('indicador_' + str(i), 'card', 20 + i * 315, 15, 300, 110,
                              {'Values': [projection('fact_operacion', measure, True)]}, measure))
    visuals += [
        visual('fallas_mes', 'clusteredColumnChart', 20, 145, 780, 300,
               {'Category': [projection('dim_tiempo', 'anio_mes')],
                'Y': [projection('fact_operacion', 'Fallas', True)]}, 'Fallas por mes · calendario simulado'),
        visual('fallas_tipo', 'clusteredBarChart', 820, 145, 440, 300,
               {'Category': [projection('dim_tipo', 'calidad')],
                'Y': [projection('fact_operacion', 'Fallas', True)]}, 'Fallas por tipo de producto'),
        visual('filtro_mes', 'slicer', 20, 475, 380, 210,
               {'Values': [projection('dim_tiempo', 'anio_mes')]}, 'Mes simulado'),
        visual('filtro_tipo', 'slicer', 420, 475, 380, 210,
               {'Values': [projection('dim_tipo', 'tipo')]}, 'Tipo de producto'),
        visual('filtro_estado', 'slicer', 820, 475, 440, 210,
               {'Values': [projection('dim_estado', 'descripcion')]}, 'Estado de falla'),
    ]
    for item in visuals:
        write_json(page / 'visuals' / item['name'] / 'visual.json', item)
    print(output / 'Mantenimiento.pbip')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--servidor', default='.\\SQLEXPRESS')
    parser.add_argument('--base', default='MantenimientoPredictivoDM')
    args = parser.parse_args()
    generate(args.servidor, args.base)
