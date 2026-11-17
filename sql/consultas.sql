SELECT t.tipo, COUNT(*) registros, SUM(f.estado_id) fallas,
 ROUND(100.0*SUM(f.estado_id)/COUNT(*),2) porcentaje_fallas, ROUND(AVG(f.torque_nm),2) torque_medio
 FROM fact_operacion f JOIN dim_tipo t USING(tipo_id) GROUP BY t.tipo ORDER BY t.tipo;