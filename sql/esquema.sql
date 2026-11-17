PRAGMA foreign_keys=ON;
DROP TABLE IF EXISTS fact_operacion;
DROP TABLE IF EXISTS dim_tipo;
DROP TABLE IF EXISTS dim_estado;
CREATE TABLE dim_tipo(tipo_id INTEGER PRIMARY KEY, tipo TEXT UNIQUE NOT NULL, calidad TEXT NOT NULL);
CREATE TABLE dim_estado(estado_id INTEGER PRIMARY KEY, descripcion TEXT NOT NULL);
CREATE TABLE fact_operacion(udi INTEGER PRIMARY KEY, product_id TEXT NOT NULL,
 tipo_id INTEGER NOT NULL REFERENCES dim_tipo(tipo_id), estado_id INTEGER NOT NULL REFERENCES dim_estado(estado_id),
 air_temperature_k REAL, process_temperature_k REAL, rotational_speed_rpm INTEGER, torque_nm REAL,
 tool_wear_min INTEGER, twf INTEGER, hdf INTEGER, pwf INTEGER, osf INTEGER, rnf INTEGER);
