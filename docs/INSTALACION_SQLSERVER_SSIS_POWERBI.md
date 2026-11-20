# Instalación y primera ejecución

## Estado de esta entrega

Se comprobaron la transformación en Python, sus pruebas automáticas, la sintaxis de PowerShell y los esquemas JSON del proyecto Power BI. Se prepararon los scripts SQL y el generador del paquete SSIS.

En el equipo revisado no se encontraron instalaciones estándar del motor SQL Server, el runtime de SSIS, Visual Studio con Integration Services ni Power BI Desktop. Por eso **todavía no se ejecutó el procedimiento SQL, no se generó ni abrió el paquete .dtsx y no se abrió ni actualizó el informe en Power BI**. La validación JSON no sustituye esa prueba de apertura. El archivo de verificación SQL solo se crea después de una carga real correcta.

## Programas necesarios

- SQL Server Developer para uso académico, con Database Engine e Integration Services. SQL Server Express por sí solo no incluye el runtime de SSIS.
- SQL Server Management Studio para consultar la base y mostrar sus tablas.
- Una versión de Visual Studio y la extensión SQL Server Integration Services Projects compatibles con el runtime de SSIS instalado. Visual Studio Code no sustituye este diseñador.
- Power BI Desktop actualizado, con soporte para proyectos PBIP/PBIR. Si la versión lo requiere, habilitar las opciones de proyecto y formato mejorado en Archivo → Opciones → Características de vista previa y reiniciar.
- Python con las dependencias de `requirements.txt`. El paquete utiliza además Windows PowerShell 5.1 y la autenticación de Windows para SQL Server.

Fuentes de instalación: [SQL Server](https://www.microsoft.com/sql-server/sql-server-downloads), [SSMS](https://learn.microsoft.com/sql/ssms/download-sql-server-management-studio-ssms), [SSIS](https://learn.microsoft.com/sql/integration-services/install-windows/install-integration-services), [Power BI Desktop](https://www.microsoft.com/download/details.aspx?id=58494).

## Preparar una sola vez

Abrir la carpeta completa en Visual Studio Code y usar su terminal PowerShell. Si se trabaja desde la copia actual:

```powershell
Set-Location 'C:\Users\diego\AppData\Local\Temp\AI4I_GitHub_20261116'
```

La copia de trabajo actual está en la ruta anterior. Antes de configurar SSIS, se recomienda copiar o clonar el proyecto a una carpeta permanente del usuario. El paquete generado guarda rutas del equipo: si se mueve la carpeta, se debe volver a generar. No se pudo crear automáticamente la carpeta permanente alternativa por falta de permisos de escritura.

Primero confirmar en SSMS el nombre del servidor al que realmente se puede conectar. `.\SQLEXPRESS` es solo el ejemplo predeterminado, no un servidor detectado. Puede ser `localhost`, `localhost\NOMBRE` u otro nombre instalado. La cuenta de Windows debe poder crear la base del proyecto o el administrador debe prepararla y conceder permisos.

Con el nombre correcto, ejecutar (sustituir `localhost` si corresponde):

```powershell
.\scripts\sqlserver\Preparar_Proyecto.ps1 -Servidor 'localhost' -Python 'C:\Users\diego\AppData\Local\Python\pythoncore-3.14-64\python.exe'
```

Esto crea `config/sqlserver.local.json` y configura los parámetros de Power BI. El archivo local no se sube a GitHub. Si ya existe, se edita en lugar de volver a crearlo. No contiene contraseñas: se utiliza autenticación de Windows.

El cifrado está activado. Si una instancia **local de práctica** tiene certificado autofirmado, se puede configurar la opción explícita `-CertificadoLocal` en la preparación inicial; solo se permite para `.`, `localhost` o `127.0.0.1`. Para servidores remotos, usar un certificado confiable. No desactivar el cifrado.

Instalar dependencias si hacen falta:

```powershell
python -m pip install -r requirements.txt
```

Si Windows bloquea scripts descargados, revisar los archivos y aplicar `Unblock-File` únicamente a los `.ps1` de este repositorio. No es necesario cambiar permanentemente la política global de PowerShell.

## Generar y ejecutar SSIS

Desde **Windows PowerShell 5.1**, con el runtime/SDK de SSIS instalado:

```powershell
.\ssis\Crear_Paquete.ps1
```

Se genera `ssis/AI4I_Carga_Full.dtsx` y se vuelve a leer para comprobar que contiene cinco tareas y cuatro conexiones de precedencia. Una vez ejecutado y revisado, se debe agregar también este archivo al repositorio como evidencia. El generador busca `Microsoft.SqlServer.ManagedDTS.dll` en las carpetas estándar de SQL Server; también acepta `-ManagedDts 'ruta completa de la DLL'` si se instaló en otro lugar. Utilizar la versión correspondiente al diseñador; no descargar DLL sueltas.

En Visual Studio, crear un proyecto **Integration Services Project** y configurar TargetServerVersion compatible con el runtime. En **SSIS Packages**, elegir **Add Existing Package → File System**, seleccionar el `.dtsx` generado y ejecutarlo. Las cinco tareas son:

1. Preparar tablas y procedimiento.
2. Extraer CSV y transformar fechas.
3. Cargar staging con SqlBulkCopy.
4. Publicar modelo estrella FULL.
5. Verificar conteos y ejecución.

SSIS coordina procesos externos; las validaciones y transformaciones están en Python y SQL. Las tareas comparten el identificador `System::ExecutionInstanceGUID`, para mantener separadas las ejecuciones. El usuario que ejecute el paquete necesita acceso al CSV, Python y permisos SQL. Si se programa posteriormente mediante SQL Server Agent, esos permisos deben aplicarse a la cuenta que ejecute el trabajo.

Para probar exactamente los mismos pasos sin abrir el diseñador:

```powershell
.\scripts\sqlserver\Datamart.ps1 -Paso Todo
```

Esta alternativa ejecuta el ETL completo desde PowerShell; no constituye evidencia de ejecución del paquete SSIS. Para la revisión que exige SSIS, conservar la evidencia de la ejecución en el diseñador.

## Comprobación del FULL

Después de ejecutar, abrir SSMS y seleccionar `MantenimientoPredictivoDM`. Ejecutar `sql/sqlserver/03_consultas_presentacion.sql`. Revisar:

| Comprobación | Resultado esperado |
|---|---:|
| `dm.fact_operacion` | 10,000 |
| `dm.dim_tipo` | 3 |
| `dm.dim_estado` | 2 |
| `dm.dim_tiempo` | 365 |
| Suma de `estado_id` en hechos | 339 |
| Fechas distintas utilizadas | 200 |
| Ejecuciones distintas en hechos | 1 |

Volver a ejecutar el paquete y comprobar que los hechos siguen siendo 10,000; `auditoria.cargas` debe tener una fila adicional. El historial no se borra en la recarga. La salida real de la verificación se guarda en `results/sqlserver/ultima_verificacion.json`; no se incluye una salida ficticia en el repositorio.

Para demostrar la protección, se pueden modificar datos **solo en una copia de prueba**: el preparador debe rechazar la entrada y la base anterior debe mantenerse. Las pruebas incluidas ya comprueban ese rechazo en archivos temporales sin modificar el original.

## Abrir Power BI

1. Después de cargar SQL Server, abrir `powerbi/Mantenimiento.pbip` con Power BI Desktop.
2. Cuando se solicite acceso a SQL Server, seleccionar autenticación de Windows y conectar al servidor configurado.
3. Elegir **Actualizar**. La conexión está en modo **Importación**: después de otra carga SQL hay que actualizar el informe de nuevo.
4. En la vista **Modelo**, comprobar tres relaciones de uno a muchos, desde cada dimensión hacia hechos, con filtro en una dirección.
5. En la vista **Informe**, probar los filtros de mes simulado, tipo y estado. Sin filtros, deben verse 10,000 observaciones, 339 fallas y 3.39% de fallas.
6. Guardar una copia `.pbix` para llevar a clase si se solicita. El `.pbip` y sus carpetas son la fuente editable del proyecto; no renombrar el archivo como `.pbix`.

Si se cambian el servidor o la base en el archivo local, volver a generar la conexión antes de abrir Power BI:

```powershell
python scripts/generar_powerbi.py --servidor 'localhost' --base 'MantenimientoPredictivoDM'
```

El generador reemplaza los archivos del informe: guardar o confirmar en Git los cambios manuales antes de usarlo nuevamente. La estructura generada fue validada contra los esquemas oficiales de Microsoft; la apertura, las consultas M y el renderizado de los visuales todavía deben comprobarse en Desktop.

## Notebooks y entrega

```powershell
python -m jupyter lab
```

Abrir `notebooks/02_ETL_SQLServer.ipynb` y ejecutar de arriba abajo. Ese notebook prepara archivos y documenta la carga, pero no borra ni publica datos SQL por sí solo.

Para Classroom, colocar el enlace del repositorio actualizado y adjuntar los documentos/notebooks que pida cada actividad. Para esta etapa conviene incluir capturas del paquete ejecutado, las consultas de verificación, la vista Modelo y el informe Power BI, una vez que esas ejecuciones se hayan realizado.
