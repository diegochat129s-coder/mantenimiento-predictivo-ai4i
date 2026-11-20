SET NOCOUNT ON;
SET XACT_ABORT ON;
IF SCHEMA_ID('dm') IS NULL EXEC('CREATE SCHEMA dm');
IF SCHEMA_ID('stg') IS NULL EXEC('CREATE SCHEMA stg');
IF SCHEMA_ID('auditoria') IS NULL EXEC('CREATE SCHEMA auditoria');
IF OBJECT_ID('dm.dim_tipo') IS NULL
CREATE TABLE dm.dim_tipo (
 tipo_id int NOT NULL PRIMARY KEY,
 tipo char(1) NOT NULL UNIQUE,
 calidad nvarchar(10) NOT NULL,
 CONSTRAINT CK_dm_tipo CHECK (tipo IN ('L','M','H'))
);
IF OBJECT_ID('dm.dim_estado') IS NULL
CREATE TABLE dm.dim_estado (
 estado_id int NOT NULL PRIMARY KEY,
 descripcion nvarchar(20) NOT NULL,
 CONSTRAINT CK_dm_estado CHECK (estado_id IN (0,1))
);
IF OBJECT_ID('dm.dim_tiempo') IS NULL
CREATE TABLE dm.dim_tiempo (
 tiempo_id int NOT NULL PRIMARY KEY,
 fecha date NOT NULL UNIQUE,
 anio int NOT NULL,
 trimestre int NOT NULL,
 mes int NOT NULL,
 mes_nombre nvarchar(12) NOT NULL,
 anio_mes char(7) NOT NULL,
 dia int NOT NULL,
 dia_semana int NOT NULL,
 dia_nombre nvarchar(12) NOT NULL,
 es_fin_semana bit NOT NULL,
 es_fecha_simulada bit NOT NULL
);
IF OBJECT_ID('auditoria.cargas') IS NULL
CREATE TABLE auditoria.cargas (
 carga_id uniqueidentifier NOT NULL PRIMARY KEY,
 fecha_carga_utc datetime2(0) NOT NULL,
 filas int NOT NULL,
 sha256_original char(64) NOT NULL,
 tipo_carga varchar(10) NOT NULL,
 discrepancias_etiquetas int NOT NULL
);
IF OBJECT_ID('dm.fact_operacion') IS NULL
CREATE TABLE dm.fact_operacion (
 udi int NOT NULL PRIMARY KEY,
 product_id varchar(20) NOT NULL UNIQUE,
 tipo_id int NOT NULL REFERENCES dm.dim_tipo(tipo_id),
 estado_id int NOT NULL REFERENCES dm.dim_estado(estado_id),
 tiempo_id int NOT NULL REFERENCES dm.dim_tiempo(tiempo_id),
 air_temperature_k decimal(7,2) NOT NULL,
 process_temperature_k decimal(7,2) NOT NULL,
 rotational_speed_rpm int NOT NULL,
 torque_nm decimal(7,2) NOT NULL,
 tool_wear_min int NOT NULL,
 twf bit NOT NULL,
 hdf bit NOT NULL,
 pwf bit NOT NULL,
 osf bit NOT NULL,
 rnf bit NOT NULL,
 fecha_carga_utc datetime2(0) NOT NULL,
 carga_id uniqueidentifier NOT NULL REFERENCES auditoria.cargas(carga_id),
 CONSTRAINT CK_dm_mediciones CHECK (air_temperature_k > 0 AND process_temperature_k >= air_temperature_k
   AND rotational_speed_rpm > 0 AND torque_nm > 0 AND tool_wear_min >= 0)
);
IF OBJECT_ID('stg.operacion') IS NULL
CREATE TABLE stg.operacion (
 carga_id uniqueidentifier NOT NULL,
 udi nvarchar(40) NULL,
 product_id nvarchar(40) NULL,
 tipo nvarchar(10) NULL,
 air_temperature_k nvarchar(40) NULL,
 process_temperature_k nvarchar(40) NULL,
 rotational_speed_rpm nvarchar(40) NULL,
 torque_nm nvarchar(40) NULL,
 tool_wear_min nvarchar(40) NULL,
 estado_id nvarchar(10) NULL,
 twf nvarchar(10) NULL,
 hdf nvarchar(10) NULL,
 pwf nvarchar(10) NULL,
 osf nvarchar(10) NULL,
 rnf nvarchar(10) NULL,
 fecha_operacion_simulada nvarchar(20) NULL
);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('stg.operacion') AND name='IX_stg_carga')
CREATE INDEX IX_stg_carga ON stg.operacion(carga_id);
