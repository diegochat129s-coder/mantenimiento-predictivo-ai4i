# Mantenimiento predictivo de maquinaria industrial

## Alumno
Diego Salinas Laguna

## Asignatura
Extracción de Conocimiento en Bases de Datos

## Recursamiento
Recursamiento 2026

## Descripción del proyecto

Este proyecto tiene como objetivo analizar información de maquinaria industrial para conocer que datos pueden estar relacionados con una posible falla.

Se revisaran datos como la temperatura, velocidad de giro, torque, desgaste de la herramienta y el estado de la maquina.

La idea es encontrar relaciones entre estos datos para despues intentar saber cuando una maquina podria presentar una falla.

## Dataset

El conjunto de datos utilizado es:

**AI4I 2020 Predictive Maintenance Dataset**

Fue obtenido de UCI Machine Learning Repository.

El dataset cuenta con aproximadamente **10,000 registros** y contiene información sobre el funcionamiento de maquinas industriales.

Archivo utilizado:

`ai4i2020.csv`

El archivo original se encuentra dentro de:

`data/raw/`

## Objetivo

Analizar los datos de las maquinas para identificar condiciones que puedan estar relacionadas con fallas.

Mas adelante se realizaran pruebas para intentar predecir valores del funcionamiento de la maquina y tambien identificar si una maquina puede fallar o no.

## Analisis que se realizaran

Durante el proyecto se trabajara principalmente con:

- Regresión para intentar calcular un valor numerico como el torque.
- Clasificación para identificar si una maquina presenta una falla o no.
- Agrupación de datos para encontrar maquinas que tengan comportamientos parecidos.

## Herramientas

Para realizar el proyecto se tiene pensado utilizar:

- Python
- Jupyter Notebook
- Visual Studio Code
- Git
- GitHub
- Pandas
- Matplotlib
- Scikit-learn

## Estructura del proyecto

- `data/raw/` contiene el dataset original.
- `notebooks/` se utilizara para realizar las pruebas y analisis.
- `src/` se utilizara para guardar archivos del proyecto.
- `docs/` guardara los documentos de las actividades.

## Estado del proyecto

Actualmente el proyecto se encuentra en la etapa de planeación de la Unidad I.
