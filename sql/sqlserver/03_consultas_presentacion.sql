-- El periodo procede de fechas simuladas con 50 observaciones por día.
SELECT COUNT(*) AS observaciones, SUM(estado_id) AS fallas FROM dm.fact_operacion;
SELECT COUNT(*) AS fechas_calendario FROM dm.dim_tiempo;
SELECT TOP (10) f.udi,t.tipo,e.descripcion,d.fecha AS fecha_simulada,f.torque_nm,f.fecha_carga_utc
FROM dm.fact_operacion f
JOIN dm.dim_tipo t ON t.tipo_id=f.tipo_id
JOIN dm.dim_estado e ON e.estado_id=f.estado_id
JOIN dm.dim_tiempo d ON d.tiempo_id=f.tiempo_id ORDER BY f.udi;
SELECT d.anio_mes,COUNT(*) AS observaciones,SUM(f.estado_id) AS fallas,
 CAST(100.0*SUM(f.estado_id)/COUNT(*) AS decimal(6,2)) AS porcentaje_fallas
FROM dm.fact_operacion f JOIN dm.dim_tiempo d ON d.tiempo_id=f.tiempo_id
GROUP BY d.anio_mes ORDER BY d.anio_mes;
SELECT t.tipo,COUNT(*) AS observaciones,SUM(f.estado_id) AS fallas
FROM dm.fact_operacion f JOIN dm.dim_tipo t ON t.tipo_id=f.tipo_id GROUP BY t.tipo ORDER BY t.tipo;
SELECT * FROM auditoria.cargas ORDER BY fecha_carga_utc DESC;
