CREATE OR ALTER PROCEDURE dm.usp_carga_full
 @carga_id uniqueidentifier,
 @sha256_original char(64)
AS
BEGIN
 SET NOCOUNT ON;
 SET XACT_ABORT ON;
 BEGIN TRY
  BEGIN TRANSACTION;
  DECLARE @lock int;
  EXEC @lock = sys.sp_getapplock @Resource='AI4I_CARGA_FULL', @LockMode='Exclusive',
    @LockOwner='Transaction', @LockTimeout=60000;
  IF @lock < 0 THROW 51001, 'Otra carga está ocupando el Data Mart.', 1;
  IF EXISTS (SELECT 1 FROM auditoria.cargas WHERE carga_id=@carga_id)
   THROW 51002, 'La carga ya fue publicada. Prepare una ejecución nueva.', 1;
  IF (SELECT COUNT(*) FROM stg.operacion WHERE carga_id=@carga_id) <> 10000
   THROW 51003, 'Se requieren 10000 filas en staging.', 1;
  SELECT TRY_CONVERT(int,udi) udi, product_id, tipo,
    TRY_CONVERT(decimal(7,2),air_temperature_k) air_temperature_k,
    TRY_CONVERT(decimal(7,2),process_temperature_k) process_temperature_k,
    TRY_CONVERT(int,rotational_speed_rpm) rotational_speed_rpm,
    TRY_CONVERT(decimal(7,2),torque_nm) torque_nm,
    TRY_CONVERT(int,tool_wear_min) tool_wear_min,
    TRY_CONVERT(int,estado_id) estado_id,
    TRY_CONVERT(int,twf) twf, TRY_CONVERT(int,hdf) hdf, TRY_CONVERT(int,pwf) pwf,
    TRY_CONVERT(int,osf) osf, TRY_CONVERT(int,rnf) rnf,
    TRY_CONVERT(date,fecha_operacion_simulada,23) fecha_operacion_simulada
  INTO #preparados FROM stg.operacion WHERE carga_id=@carga_id;
  IF EXISTS (SELECT 1 FROM #preparados WHERE
    udi IS NULL OR udi NOT BETWEEN 1 AND 10000
    OR tipo IS NULL OR tipo NOT IN ('L','M','H')
    OR product_id IS NULL OR LEN(product_id) < 2 OR LEN(product_id) > 20
    OR LEFT(product_id,1) <> tipo
    OR air_temperature_k IS NULL OR air_temperature_k <= 0
    OR process_temperature_k IS NULL OR process_temperature_k < air_temperature_k
    OR rotational_speed_rpm IS NULL OR rotational_speed_rpm <= 0
    OR torque_nm IS NULL OR torque_nm <= 0
    OR tool_wear_min IS NULL OR tool_wear_min < 0
    OR estado_id IS NULL OR estado_id NOT IN (0,1)
    OR twf IS NULL OR twf NOT IN (0,1) OR hdf IS NULL OR hdf NOT IN (0,1)
    OR pwf IS NULL OR pwf NOT IN (0,1) OR osf IS NULL OR osf NOT IN (0,1)
    OR rnf IS NULL OR rnf NOT IN (0,1)
    OR fecha_operacion_simulada IS NULL
    OR fecha_operacion_simulada <> DATEADD(day,(udi-1)/50,CONVERT(date,'20260101',112)))
   THROW 51004, 'Datos inválidos o fechas distintas de la regla de simulación.', 1;
  IF EXISTS (SELECT udi FROM #preparados GROUP BY udi HAVING COUNT(*) > 1)
     OR EXISTS (SELECT product_id FROM #preparados GROUP BY product_id HAVING COUNT(*) > 1)
   THROW 51005, 'Identificadores duplicados.', 1;
  IF @sha256_original IS NULL OR LEN(@sha256_original) <> 64
   THROW 51006, 'Se requiere la huella SHA256 del original.', 1;

  -- Se publican dimensiones y hechos dentro de la misma transacción.
  DELETE FROM dm.fact_operacion;
  DELETE FROM dm.dim_tipo;
  DELETE FROM dm.dim_estado;
  DELETE FROM dm.dim_tiempo;
  INSERT dm.dim_tipo VALUES (1,'L',N'Baja'),(2,'M',N'Media'),(3,'H',N'Alta');
  INSERT dm.dim_estado VALUES (0,N'Sin falla'),(1,N'Con falla');
  DECLARE @fecha date = '20260101';
  WHILE @fecha <= '20261231'
  BEGIN
   DECLARE @semana int = (DATEDIFF(day,CONVERT(date,'19000101',112),@fecha) % 7) + 1;
   INSERT dm.dim_tiempo VALUES (
    CONVERT(int,CONVERT(char(8),@fecha,112)), @fecha, YEAR(@fecha), DATEPART(quarter,@fecha), MONTH(@fecha),
    CHOOSE(MONTH(@fecha),N'Enero',N'Febrero',N'Marzo',N'Abril',N'Mayo',N'Junio',N'Julio',N'Agosto',N'Septiembre',N'Octubre',N'Noviembre',N'Diciembre'),
    CONVERT(char(7),@fecha,126), DAY(@fecha), @semana,
    CHOOSE(@semana,N'Lunes',N'Martes',N'Miércoles',N'Jueves',N'Viernes',N'Sábado',N'Domingo'),
    CASE WHEN @semana IN (6,7) THEN 1 ELSE 0 END,1);
   SET @fecha = DATEADD(day,1,@fecha);
  END;
  DECLARE @momento datetime2(0) = SYSUTCDATETIME();
  DECLARE @discrepancias int = (SELECT COUNT(*) FROM #preparados WHERE estado_id <>
    CASE WHEN twf+hdf+pwf+osf+rnf > 0 THEN 1 ELSE 0 END);
  INSERT auditoria.cargas VALUES (@carga_id,@momento,10000,@sha256_original,'FULL',@discrepancias);
  INSERT dm.fact_operacion
  SELECT udi,product_id,CASE tipo WHEN 'L' THEN 1 WHEN 'M' THEN 2 ELSE 3 END,estado_id,
   CONVERT(int,CONVERT(char(8),fecha_operacion_simulada,112)),
   air_temperature_k,process_temperature_k,rotational_speed_rpm,torque_nm,tool_wear_min,
   twf,hdf,pwf,osf,rnf,@momento,@carga_id
  FROM #preparados;
  IF (SELECT COUNT(*) FROM dm.fact_operacion) <> 10000
   THROW 51007, 'El conteo final no coincide.', 1;
  DELETE FROM stg.operacion WHERE carga_id=@carga_id;
  COMMIT;
 END TRY
 BEGIN CATCH
  IF @@TRANCOUNT > 0 ROLLBACK;
  THROW;
 END CATCH;
END;
