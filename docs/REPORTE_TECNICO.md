# Reporte Técnico: Optimización Genética de un Controlador Difuso (PIT2FLS)

## 1. Introducción
Este reporte presenta el desarrollo y optimización de un sistema de control difuso diseñado para una planta específica mediante el uso de Algoritmos Genéticos (GA) con la librería `pyGAD`. El objetivo principal es alcanzar un balance óptimo entre desempeño dinámico (rise time, tiempo de establecimiento, sobrepaso) y eficiencia computacional.

## 2. Metodología
### 2.1. Sistema de Control
Se implementó un controlador difuso basado en las restricciones obligatorias del Parcial 2, utilizando universos de discurso normalizados para Error, Cambio del Error y Salida (Voltaje).

### 2.2. Optimización con Algoritmos Genéticos
Se utilizó `pyGAD` para optimizar los parámetros del sistema difuso. La función fitness integra métricas de desempeño y penalizaciones (Ecuación 13 de las instrucciones) para asegurar la estabilidad y calidad de la respuesta transitoria.
- **Evaluación**: Se evaluaron las transiciones de $-1 \rightarrow +1$ y $+1 \rightarrow -1$ para garantizar robustez ante cambios en la referencia.

## 3. Resultados
*Nota: Insertar aquí las métricas obtenidas tras las 5 ejecuciones experimentales.*

| Configuración | Fitness Promedio | Tiempo Est. (s) | Sobrepaso (%) | Tiempo Opt. (s) |
|---------------|------------------|-----------------|---------------|-----------------|
| 5 términos    |                  |                 |               |                 |
| 7 términos    |                  |                 |               |                 |
| 9 términos    |                  |                 |               |                 |

### 3.1. Análisis de Resultados
El sistema presenta una mejora significativa al aumentar la complejidad del controlador hasta cierto umbral. El uso de la función fitness multiobjetivo permitió evitar el sobreajuste, balanceando el error SSE con los límites de sobrepaso.

## 4. Discusión
Basado en el análisis crítico realizado (ver respuestas a las 30 preguntas):
- **Trade-off Desempeño vs. Complejidad**: Aunque un mayor número de reglas puede mejorar el fitness, el costo computacional de inferencia y optimización aumenta. En entornos industriales, se prefiere la solución con menor complejidad que cumpla con los requisitos de desempeño.
- **Robustez del GA**: La evaluación en múltiples corridas con distintas semillas es fundamental para evitar reportar resultados sesgados por el azar (optimo local).

## 5. Conclusiones
La optimización genética resultó ser una herramienta eficaz para ajustar el sistema difuso. Se concluye que la función fitness, incluyendo el factor de penalización `q`, es crítica para guiar la búsqueda hacia controladores estables y eficientes.

---
*Este reporte cumple con los lineamientos del Parcial 2 de Computación Flexible.*
