# Instrucciones del Parcial 2 — Computación Flexible

> Texto extraído de `Parcial 2.pdf` (17 páginas) con `pdftotext -layout`. Sirve como contexto legible del enunciado para agentes y colaboradores.
> Archivo fuente: `/home/m4r10/Documents/OMSDMAG/Parcial 2.pdf`.

## Parcial 2 — Computación Flexible

Optimización Multiobjetivo de Sistemas Difusos mediante Algoritmos Genéticos con pyGAD

### Objetivo

Utilizar la biblioteca pyGAD para optimizar automáticamente sistemas de inferencia difusa tipo Mamdani empleados para el control de un servomotor de corriente directa. La optimización deberá realizarse simultáneamente sobre:

- Los parámetros de las funciones de membresía de entrada.

- Los parámetros de las funciones de membresía de salida.

- El conjunto de reglas difusas utilizado por el controlador.

El propósito de esta actividad es analizar cómo la complejidad estructural de un sistema difuso afecta:

- El desempeño dinámico del controlador.

- La complejidad del sistema difuso.

- El costo computacional asociado a la optimización.

- El costo computacional asociado a la inferencia.

### Descripción de la actividad

# PARTE 1. SISTEMA DE CONTROL, PLANTA Y BASELINES

### Sistema a Controlar

Todos los experimentos deberán realizarse utilizando exactamente el servomotor estudiado en clase y en actividades previas. La función de transferencia de la planta es:

$$G(s) = \\frac{0.5}{s^3 + 13.6667\\,s^2 + 23.3487\\,s}$$

donde:

- Entrada: voltaje aplicado al servomotor.

- Salida: posición angular del rotor.

No se permite modificar la planta ni utilizar sistemas dinámicos alternativos.

## Restricción sobre la Simulación de la Planta

Con el objetivo de garantizar que todos los equipos evalúen exactamente el mismo sistema dinámico bajo las mismas condiciones numéricas, la simulación de la planta deberá realizarse exclusivamente mediante funciones de la biblioteca SciPy.

### Herramientas Obligatorias

La planta deberá implementarse utilizando exactamente:

donde:

```python
from scipy.signal import lti, lsim
```

- lti deberá emplearse para definir la función de transferencia del servomotor.

- lsim deberá emplearse para simular la respuesta temporal del sistema.

### Implementación esperada

La función de transferencia deberá construirse utilizando:

La respuesta temporal deberá obtenerse mediante:

donde:

```python
G = lti([0.5], [1, 13.6667, 23.3487, 0])
tout, yout, xout = lsim(G, U=u, T=t )
```

- u corresponde al voltaje generado por el controlador difuso.

- t corresponde al vector temporal de simulación.

- yout corresponde a la posición angular del rotor.

## Restricción Obligatoria

La simulación del servomotor deberá realizarse exclusivamente mediante: scipy.signal.lsim No se permite utilizar:

- MATLAB Simulink.

- Control System Toolbox de MATLAB.

- odeint.

- solve_ivp.

- Integradores numéricos desarrollados por el estudiante.

- Métodos de discretización manual.

- Bibliotecas de control distintas de scipy.signal.

- Herramientas externas de simulación.

### Justificación

El objetivo de esta restricción es garantizar que:

- Todos los estudiantes evalúen exactamente la misma planta.

- Todas las diferencias observadas provengan únicamente de:

- o la estructura del sistema difuso,

- o el número de términos lingüísticos,

- o las funciones de membresía,

- o las reglas difusas,

- o y el proceso de optimización genética.

### Configuraciones Difusas Obligatorias

Cada equipo deberá diseñar, optimizar y comparar tres sistemas difusos distintos.

| Controlador A | Controlador B | Controlador C |
|---|---|---|
| 5 términos lingüísticos por entrada | 7 términos lingüísticos por entrada | 9 términos lingüísticos por entrada |
| NB, NS, ZE, PS, PB | NB, NM, NS, ZE, PS, PM, PB | NVB, NB, NM, NS, ZE, PS, PM, PB, PVB |

Los nombres de los términos pueden modificarse libremente.


Todos los controladores deberán utilizar exactamente:

- **Entrada 1 — Error:** $e(t) = r(t) - \\theta(t)$
- **Entrada 2 — Cambio del error:** $\\Delta e(t) = \\frac{de(t)}{dt}$
- **Salida — Voltaje aplicado al servomotor:** $v(t)$

No se permite agregar variables adicionales.

### Restricciones Experimentales Obligatorias

El incumplimiento de cualquiera de las siguientes restricciones invalidará los resultados obtenidos.

### Tiempo de simulación

Todos los experimentos deberán realizarse utilizando exactamente: 𝑇𝑠𝑖𝑚 = 200 𝑠

No se permite reducir ni ampliar el horizonte temporal de simulación.

### Señal de referencia

Todos los experimentos deberán utilizar exactamente la siguiente referencia:

- Tipo: señal cuadrada.

- Amplitud: ±1 radián.

- Período: 100 segundos.

- Ciclo útil: 50%.

Por lo tanto

𝑟(𝑡) ∈ {−, 1 + 1}

y cambiará de signo cada 50 segundos. No se permite:

- Modificar la amplitud.

- Modificar la frecuencia.

- Utilizar una señal escalón.

- Utilizar señales senoidales.

- Utilizar señales triangulares.

- Utilizar señales rampa.

### Ausencia de ruido

A diferencia de algunos experimentos reportados en el artículo de referencia, en este examen queda estrictamente prohibido introducir ruido en cualquier parte del sistema. No se permitirá:

- Ruido blanco.

- Ruido gaussiano.

- Perturbaciones externas.

- Distorsiones artificiales de la referencia.

- Señales aleatorias adicionadas al sistema.

El objetivo del examen es evaluar exclusivamente el efecto de:

- número de términos lingüísticos,

- diseño de funciones de membresía,

- selección de reglas difusas,

- optimización evolutiva.

### Universos de Discurso Obligatorios

Los universos de discurso deberán permanecer fijos durante toda la optimización.

### Error

$$e \\in [-\\pi/2,\\; \\pi/2]$$

### Cambio del Error

$$\\Delta e \\in [-\\pi/6,\\; \\pi/6]$$

### Voltaje

$$v \\in [-8.18,\\; 8.18]$$

No se permite:

- Escalamiento dinámico.

- Ajuste automático de rangos.

- Modificación de universos de discurso.

- Expansión o reducción de límites durante la optimización.

# PARTE 2. OPTIMIZACIÓN GENÉTICA Y FUNCIÓN FITNESS

El algoritmo genético deberá optimizar simultáneamente:

```text
Variables a Optimizar mediante pyGAD
```

### Funciones de membresía de entrada

Para cada variable de entrada:

- Posición de los centros.

- Anchura de las funciones de membresía.

- Solapamiento entre conjuntos difusos.

- Forma de las funciones de membresía.

### Funciones de membresía de salida

Para la variable de salida:

- Posición de los centros.

- Anchura de las funciones de membresía.

- Solapamiento entre conjuntos difusos.

- Forma de las funciones de membresía.

### Base de reglas difusas

El cromosoma deberá permitir:

- Activar reglas.

- Desactivar reglas.

Por lo tanto, el número final de reglas activas deberá ser resultado del proceso evolutivo. No se permite utilizar una base de reglas fija durante toda la optimización.

### Restricciones sobre la Base de Reglas

El algoritmo genético podrá modificar únicamente:

- La activación o desactivación de reglas.

- Los consecuentes asociados a las reglas.

- Los parámetros de las funciones de membresía.

No se permite:

- Crear variables nuevas.

- Crear antecedentes inexistentes.

- Crear consecuentes fuera del universo de discurso definido.

- Modificar el número de entradas del controlador.

- Modificar el número de salidas del controlador.

### Restricciones sobre las Funciones de Membresía

Las funciones de membresía deberán permanecer siempre dentro de sus respectivos universos de discurso. No se aceptarán individuos que produzcan:

- Centros fuera de rango.

- Anchuras negativas.

- Funciones invertidas.

- Funciones degeneradas.

- Funciones matemáticamente inválidas.

Los estudiantes deberán implementar mecanismos de:

- reparación del cromosoma,

- penalización directa del fitness.

### Función Fitness Obligatoria

Todos los individuos deberán evaluarse utilizando la función multiobjetivo transitoria propuesta en el artículo de referencia. La función fitness deberá implementarse obligatoriamente como:

$$
f_i = w_1\frac{1}{1+|OS_i^+|} + w_2\frac{1}{1+|SSE_i^+|} + w_3\frac{tr_0}{q+tr_i^+} + w_4\frac{ts_0}{ts_i^+}
     + w_5\frac{1}{1+|OS_i^-|} + w_6\frac{1}{1+|SSE_i^-|} + w_7\frac{tr_0}{q-tr_i^-} + w_8\frac{ts_0}{ts_i^-}
$$

donde:

```text
      •      𝑂𝑆𝑖 = Overshoot.
      •      𝑆𝑆𝐸𝑖 = Error en estado estable.
      •      𝑡𝑟𝑖 = Tiempo de crecimiento.
       •     𝑡𝑠𝑖 = Tiempo de establecimiento.
```

- 𝑞= Factor de penalización.

### Constantes Obligatorias

De acuerdo con la metodología propuesta en el artículo, deberán utilizarse exactamente los siguientes valores: 𝑡𝑟0 = 9 𝑠 𝑡𝑠0 = 13 𝑠 Estos valores no podrán:

- modificarse,

- optimizarse,

- ajustarse manualmente.

Su modificación invalidará los resultados experimentales.

### Pesos de la Función Fitness

La elección de los pesos: 𝑤1 , 𝑤2 , 𝑤3 , 𝑤4 , 𝑤5 , 𝑤6 , 𝑤7 , 𝑤8 deberá justificarse técnicamente. Los estudiantes podrán:

- utilizar pesos iguales o

- proponer otra combinación,

siempre que exista una justificación técnica sustentada. Deberá cumplirse: 𝑤1 + 𝑤2 + 𝑤3 + 𝑤4 + 𝑤5 + 𝑤6 + 𝑤7 + 𝑤8 = 1

### Penalización Obligatoria (Ecuación 13)

Todos los equipos deberán implementar obligatoriamente el factor de penalización:

$$q = \\frac{\\max(h^0) - \\min(h_i)}{\\max(h) - \\min(h)}$$

donde:

- ℎ representa la respuesta temporal del sistema (revisar artículo de referencia).

- ℎ0 representa la señal de referencia.

### Justificación del Factor de Penalización

El propósito de la Ecuación (13) es evitar que el algoritmo genético favorezca individuos que aparentan poseer tiempos de crecimiento extremadamente pequeños cuando en realidad:

- no alcanzan la referencia,

- alcanzan solo una fracción de ella,

- generan respuestas físicamente inaceptables.

Por lo tanto, el uso del factor 𝑞 es obligatorio.

### Evaluación Obligatoria de las Dos Transiciones

Debido a que:

- la referencia es cuadrada,

- el período es de 100 segundos,

- la simulación dura exactamente 200 segundos,

la función fitness deberá evaluar obligatoriamente las transiciones positiva y negativa. No se aceptará evaluar únicamente una parte de la simulación.

−1 → +1                          +1 → −1

𝑆𝑆𝐸 −

**Tabla 1. Métricas de desempeño de los controladores**

| Variable | Transición Positiva ($-1 \\to +1$) | Transición Negativa ($+1 \\to -1$) |
|---|---|---|
| Overshoot | $OS^+$ | $OS^-$ |
| Error en estado estable | $SSE^+$ | $SSE^-$ |
| Tiempo de crecimiento | $t_r^+$ | $t_r^-$ |
| Tiempo de establecimiento | $t_s^+$ | $t_s^-$ |

### NOTA: Descarte las mediciones de la transición de 0 a 1 inicial.

## Restricción Fundamental de Evaluación

No se aceptarán implementaciones que:

- simulen menos de 200 segundos (para poder evaluar todas las métricas de desempeño),

- evalúen únicamente la transición positiva,

- evalúen únicamente la transición negativa,

- sustituyan la señal cuadrada por una señal escalón,

- eliminen el factor de penalización 𝑞,

- modifiquen 𝑡𝑟0 = 9s,

- modifiquen 𝑡𝑠0 = 13s, e

- introduzcan ruido en cualquier parte del sistema.

Para cada individuo seleccionado como mejor solución, deberán reportarse explícitamente todas las 8 métricas de la Tabla 1 y adicionalmente:

```text
Reporte Obligatorio de Métricas
```

- Fitness total.

- El número y exactamente qué reglas quedaron activas.

- Tiempo de inferencia.

- Tiempo de optimización.

# PARTE 3. PROTOCOLO EXPERIMENTAL, COMPARACIÓN Y ENTREGABLES

### Protocolo Experimental Obligatorio

Todos los experimentos deberán seguir exactamente el protocolo descrito a continuación. El incumplimiento de cualquiera de las fases invalidará la comparación experimental.

## Fase 1. Implementación de los Controladores Base

Antes de realizar cualquier proceso de optimización genética, cada equipo deberá implementar los siguientes tres controladores difusos:

Los tres controladores deberán evaluarse inicialmente sin optimización genética. Para cada uno deberán registrarse todas las métricas de desempeño de la Tabla 1, Fitness total, número de reglas totales (usando todas las reglas) y tiempo de inferencia.

```text
    • Controlador A. Sistema difuso con: 5 términos lingüísticos por entrada (generados con automf)
    • Controlador B. Sistema difuso con: 7 términos lingüísticos por entrada (generados con automf)
    • Controlador C. Sistema difuso con: 9 términos lingüísticos por entrada (generados con automf)
```

## Fase 2. Optimización mediante pyGAD

La optimización deberá realizarse exclusivamente mediante pygad No se permite el uso de:

- DEAP

- Nevergrad

- Optuna

- Hyperopt

- Algoritmos evolutivos implementados por terceros ni propios

### Configuración mínima obligatoria

La optimización deberá utilizar como mínimo:

- 20 individuos.

- 30 generaciones.

Los estudiantes podrán utilizar poblaciones o números de generaciones mayores, pero nunca menores.

### Evaluación de cada individuo

Cada individuo deberá evaluarse mediante:

- simulación completa de 200 segundos,

- referencia cuadrada completa,

- cálculo de las ocho métricas transitorias,

- aplicación obligatoria de las Ecuaciones (12) y (13).

No se aceptará ningún mecanismo de evaluación simplificada.

## Fase 3. Selección del Mejor Individuo

Al finalizar el proceso evolutivo deberá seleccionarse:

La selección deberá realizarse utilizando exclusivamente la función fitness definida anteriormente.

```text
     • el mejor individuo del sistema de 5 términos;
     • el mejor individuo del sistema de 7 términos;
     • el mejor individuo del sistema de 9 términos.
```

## Fase 4. Evaluación del Costo Computacional

Además de las métricas de control, deberá realizarse una evaluación cuantitativa del costo computacional. Como mínimo deberán medirse:

- Tiempo total de optimización: Tiempo requerido para completar todas las generaciones del

algoritmo genético.

- Tiempo promedio de inferencia: Tiempo promedio requerido para generar una salida del

controlador difuso.

- Número de parámetros optimizados: Cantidad total de genes presentes en el cromosoma.

- El número y qué exactamente qué reglas quedaron activas: Cantidad de reglas finalmente

utilizadas por la mejor solución encontrada y además cuáles fueron seleccionadas.

- Uso de memoria: Uso aproximado de memoria asociado al controlador obtenido.

## Fase 5. Repetibilidad Experimental

Los algoritmos genéticos son métodos estocásticos. Por esta razón, todos los experimentos deberán repetirse como mínimo: 5 veces utilizando semillas aleatorias distintas.

## Restricción de Repetibilidad

No se aceptará reportar únicamente la mejor corrida. Cada estudiante deberá reportar:

- promedio,

- desviación estándar,

de todas las métricas obtenidas durante las cinco ejecuciones.

### Comparación Final Obligatoria

La comparación experimental deberá realizarse entre:

Utilizando exactamente:

```text
     • Sistema difuso de 5 términos.
     • Sistema difuso de 7 términos.
     • Sistema difuso de 9 términos.
```

- la misma planta,

- la misma referencia,

- los mismos universos de discurso,

- el mismo tiempo de simulación,

- la misma metodología de optimización.

## Tabla Obligatoria de Resultados

La siguiente tabla deberá aparecer obligatoriamente en el reporte.

| Métrica | 5 términos | 7 términos | 9 términos |
|---|---|---|---|
| Fitness promedio | | | |
| Fitness máximo | | | |
| $OS^+$ | | | |
| $OS^-$ | | | |
| $SSE^+$ | | | |
| $SSE^-$ | | | |
| $t_r^+$ | | | |
| $t_r^-$ | | | |
| $t_s^+$ | | | |
| $t_s^-$ | | | |
| Reglas activas | Ej. 1. A→B, 2. B→C, ... | | |
| Número de parámetros optimizados | | | |
| Tiempo de optimización (s) | | | |
| Tiempo promedio de inferencia (ms) | | | |
| Uso de memoria (MB) | | | |

```text
     Métrica                                        5 términos       7 términos   9 términos
```

### Análisis Obligatorio

Los estudiantes deberán discutir:

- La influencia del número de términos lingüísticos.

- La influencia del número de reglas activas.

- La influencia de las funciones de membresía.

- La evolución del fitness.

- El impacto del costo computacional.

- El compromiso entre desempeño y complejidad.

No será suficiente reportar únicamente tablas de resultados.

### Entregables

### Código

El estudiante deberá entregar:

- Libreta .ipynb

completamente funcional.

### Reporte

El reporte deberá entregarse en formato:

- PDF o DOCX

- Reporte integrado en la libreta

### Estructura Obligatoria del Reporte

1. Introducción                                    4. Discusión Incluir como mínimo:                               Analizar:

- Sistemas difusos.                               • Influencia del número de términos.

- Control difuso.                                 • Influencia del número de reglas.

- Algoritmos genéticos.                           • Impacto de las membresías obtenidas.

- pyGAD.                                          • Robustez de las soluciones.

- Optimización multiobjetivo.                     • Costos computacionales observados.

2. Metodología                                     5. Conclusiones Describir:                                         Discutir:

- Diseño de los controladores.                    • Hallazgos principales.

- Universos de discurso.                          • Limitaciones observadas.

- Funciones de membresía.                         • Recomendaciones para trabajos

- Codificación genética.                              futuros.

- Operadores evolutivos.

- Función fitness.

- Parámetros de optimización.

3. Resultados Incluir:

- Mejor cromosoma encontrado.

- Evolución del fitness.

- Gráficas de convergencia.

- Curvas de respuesta temporal.

- Tabla comparativa obligatoria.

- Análisis estadístico de las cinco

ejecuciones.

## Nota Metodológica Importante

La comparación entre los tres controladores sólo será válida si todos los experimentos utilizan exactamente:

- la misma planta;

- la misma referencia cuadrada;

- el mismo tiempo de simulación;

- los mismos universos de discurso;

- las mismas métricas de evaluación;

- la misma función fitness;

- el mismo simulador (scipy.signal.lsim).

Cualquier desviación de estas condiciones invalidará la comparación experimental.

# PARTE 4. CÓDIGO BASE OBLIGATORIO Y ESTRUCTURA MÍNIMA DEL PROYECTO

El propósito de esta sección es establecer una estructura mínima común para todos los proyectos, garantizando que la comparación entre equipos sea válida y reproducible. El siguiente código NO resuelve el examen.

Únicamente proporciona una base mínima para:

- Crear la planta.

- Generar la señal de referencia.

- Simular el sistema utilizando lsim.

- Obtener el error y el cambio del error.

- Integrar posteriormente el controlador difuso y el algoritmo genético.

**Bibliotecas Permitidas** (se permite utilizar):

- numpy
- scipy
- scikit-fuzzy
- pygad
- matplotlib
- time
- timeit

**Bibliotecas Obligatorias** (todos los proyectos deberán incluir):

- lti
- lsim
- scipy.signal.square
- skfuzzy
- skfuzzy.control
- pygad

### Creación de la Planta

La planta deberá implementarse exactamente como:

No se acepta ninguna modificación.

```python
       G = lti([0.5], [1, 13.6667, 23.3487, 0])
```

### Vector de Tiempo

La simulación deberá realizarse durante: $T_{sim} = 200\\,s$. Ejemplo:

```python
dt = 0.01
t = np.arange(0, 200 + dt, dt)
```

La resolución temporal podrá modificarse, siempre que:

- se justifique técnicamente;

- la simulación cubra exactamente los 200 s.

### Señal de Referencia

La señal de referencia deberá ser una señal cuadrada de:

- amplitud ±1 rad;

- período de 100 s;

- ciclo útil del 50%.

Ejemplo:

```python
       r = square(2*np.pi*t/100)
```

### Condiciones Iniciales

Las condiciones iniciales deberán ser:

```python
       x0 = [0, 0, 0]
```

### Simulación de la Planta

La respuesta temporal deberá obtenerse exclusivamente mediante:

donde:

```python
       tout, theta, xout = lsim(G, U=u, T=t, X0=x0)
```

- u es el voltaje generado por el controlador difuso.

- theta es la posición angular del rotor.

### Cálculo del Error

El error deberá calcularse mediante:

```python
        e = r - theta
```

### Cambio del Error

El cambio del error deberá calcularse utilizando diferencias finitas. Ejemplo:

```python
      de = np.diff(e, prepend=e[0]) / dt
```

### Universos de Discurso Obligatorios

Deberán declararse exactamente:

```python
ERROR_MIN = -np.pi/2
ERROR_MAX = np.pi/2

DERROR_MIN = -np.pi/6
DERROR_MAX = np.pi/6

VOLTAGE_MIN = -8.18
VOLTAGE_MAX = 8.18
```

No podrán modificarse.

```python
      ERROR_MIN = -np.pi/2
       DERROR_MIN = -np.pi/6
      VOLTAGE_MIN = -8.18
```

Ejemplo:

```text
Definición de Variables Difusas
```

```python
       error = ctrl.Antecedent(np.linspace(ERROR_MIN, ERROR_MAX, 1000), 'error')
       derror = ctrl.Antecedent(np.linspace(DERROR_MIN, DERROR_MAX, 1000), 'derror')
       voltage = ctrl.Consequent(np.linspace(VOLTAGE_MIN, VOLTAGE_MAX, 1000), 'voltage')
```

### Codificación Genética Sugerida

El cromosoma deberá incluir al menos:

**Parámetros de membresías:**

- centros
- anchuras
- solapamientos

**Reglas:**

- activada = 1
- desactivada = 0

### Estructura General de la Función Fitness

El fitness deberá:

1. Construir el sistema difuso.
2. Simular los 200 segundos completos.
3. Calcular métricas de rendimiento.
4. Calcular penalizaciones.
5. Calcular la función fitness.

### Configuración Mínima de pyGAD

La optimización deberá utilizar al menos:

```python
sol_per_pop = 20
num_generations = 30
```

### Medición Obligatoria del Tiempo de Optimización

Ejemplo:

```python
start = time.time()
ga_instance.run()
end = time.time()
optimization_time = end - start
```

### Medición Obligatoria del Tiempo de Inferencia

Ejemplo:

```python
start = time.perf_counter()
controller.compute()
end = time.perf_counter()
inference_time = end - start
```

### Salidas Obligatorias del Proyecto

Cada ejecución deberá generar:

- Curva de convergencia. Generación vs Fitness

- Respuesta temporal. Referencia vs Salida

- Mejor cromosoma encontrado. Parámetros optimizados

## Restricción Final

El código entregado deberá ser completamente reproducible. El docente deberá ser capaz de ejecutar:

- python main.py ó

- Run All en una libreta Jupyter

y obtener todos los resultados reportados en el documento sin modificaciones adicionales.

# PARTE 5. PREGUNTAS DE ANÁLISIS CRÍTICO

### Instrucciones

Las siguientes preguntas tienen como propósito evaluar su capacidad para:

- Interpretar resultados experimentales.

- Detectar limitaciones metodológicas.

- Analizar compromisos entre desempeño y complejidad.

- Cuestionar críticamente las decisiones de diseño.

- Sustentar conclusiones mediante evidencia experimental.

No se aceptarán respuestas basadas únicamente en opiniones personales. Todas las respuestas deberán apoyarse en:

- resultados obtenidos durante el examen;

- métricas experimentales;

- gráficas;

- tablas comparativas;

- evidencia cuantitativa.

Las preguntas son las siguientes:

afirmarse que es la mejor solución? Justifique utilizando evidencia experimental. 2. Muchos estudiantes asumen que incrementar el número de términos lingüísticos siempre mejora el desempeño del controlador. ¿Sus resultados experimentales respaldan esta afirmación? Explique. 3. ¿Qué efecto tiene el aumento del número de términos lingüísticos sobre:

```text
   1. Si el controlador de 9 términos lingüísticos obtiene el mayor fitness de todos los experimentos,
       pero requiere diez veces más tiempo de optimización que el controlador de 5 términos, ¿puede
```

- el tamaño del espacio de búsqueda,

- el número de parámetros optimizables,

- y la dificultad del proceso de optimización?

4. Si dos controladores presentan prácticamente el mismo fitness final pero uno utiliza menos de la mitad de las reglas activas, ¿cuál debería preferirse? Justifique. 5. ¿Un mayor número de reglas implica necesariamente una mejor capacidad de control? Utilice resultados experimentales para sustentar su respuesta. 6. Si durante la optimización genética algunas reglas son eliminadas y el fitness mejora, ¿qué puede concluir acerca de dichas reglas? 7. ¿Es posible que algunas reglas consideradas intuitivamente importantes resulten irrelevantes durante la optimización? Explique por qué. 8. Suponga que un controlador obtiene:

- el menor overshoot de todos los experimentos,

pero también:

- el mayor tiempo de establecimiento.

¿Puede considerarse superior? Justifique. 9. ¿Por qué la función fitness utilizada en este examen considera simultáneamente:

```text
       • Overshoot,
```

- SSE,

- Rise Time,

- Settling Time,

en lugar de utilizar únicamente SSE? 10. ¿Qué problemas aparecerían si la función fitness utilizara únicamente 𝑆𝑆𝐸 como criterio de evaluación? 11. ¿Qué problemas aparecerían si la función fitness utilizara únicamente 𝑅𝑀𝑆𝐸 como criterio de evaluación? 12. ¿Qué ventajas aporta la incorporación del factor de penalización 𝑞 de la Ecuación (13)? Explique utilizando ejemplos observados durante la optimización. 13. Suponga que durante la optimización aparece un individuo con un tiempo de crecimiento extremadamente pequeño. ¿Qué verificaciones adicionales deben realizarse antes de considerar que realmente es una buena solución? 14. ¿Por qué este examen exige evaluar la transición:

−1 → +1 y también: +1 → −1

en lugar de utilizar únicamente una señal escalón? 15. Si solamente se evaluara la transición positiva, ¿qué comportamientos potencialmente problemáticos podrían pasar desapercibidos? 16. ¿Puede existir sobreajuste en un sistema difuso optimizado mediante algoritmos genéticos? Explique cómo podría manifestarse en este problema específico. 17. Suponga que después de 30 generaciones el fitness deja de mejorar. ¿Qué posibles explicaciones existen? Mencione al menos tres. 18. Si se duplicara el tamaño de la población del algoritmo genético: ¿estaría garantizado encontrar una mejor solución? Justifique. 19. Si se duplicara el número de generaciones: ¿estaría garantizado encontrar una mejor solución? Justifique. 20. Durante la optimización genética pueden aparecer individuos claramente peores que sus padres. ¿Por qué la mutación sigue siendo necesaria? 21. ¿Qué información proporciona el tiempo de establecimiento que no proporciona el tiempo de crecimiento? 22. Dos controladores presentan exactamente los mismos valores de:

```text
    • Overshoot
```

- SSE

- Rise Time

- Settling Time

pero uno requiere tres veces más tiempo de inferencia. ¿Cuál utilizaría en una aplicación industrial real? Justifique.

```text
23. Suponga que el controlador con 9 términos mejora el fitness promedio únicamente un 1%
    respecto al controlador de 5 términos, pero requiere:
```

- cuatro veces más memoria,

- ocho veces más tiempo de optimización,

- tres veces más tiempo de inferencia.

¿Considera que dicha mejora es significativa? Explique. 24. ¿La solución encontrada por pyGAD puede considerarse necesariamente un óptimo global? Explique utilizando los conceptos de:

- exploración,

- explotación,

- óptimo local,

- óptimo global.

25. ¿Por qué este examen exige realizar al menos 5 ejecuciones independientes utilizando semillas distintas? ¿Qué problema metodológico se intenta evitar? 26. Si un estudiante reporta únicamente la mejor corrida obtenida durante sus experimentos: ¿por qué sus conclusiones podrían ser engañosas?

27. Durante la optimización observó que distintas ejecuciones generan controladores completamente diferentes pero con fitness similares. ¿Qué indica esto acerca del espacio de búsqueda? 28. ¿Considera que existe un número óptimo de términos lingüísticos para este problema? Argumente utilizando los resultados obtenidos. 29. Con base en sus resultados experimentales:

```text
        • compare los controladores de 5, 7 y 9 términos;
```

- analice sus ventajas y desventajas;

- discuta el impacto del costo computacional;

- determine cuál representa el mejor equilibrio entre desempeño y complejidad.

La respuesta deberá sustentarse mediante evidencia experimental. 30. Durante muchos años una gran parte de la investigación en inteligencia artificial y control se enfocó principalmente en maximizar el desempeño de los sistemas. Sin embargo, en aplicaciones reales también resultan importantes aspectos como:

- complejidad computacional,

- tiempo de ejecución,

- consumo de memoria,

- facilidad de mantenimiento,

- interpretabilidad del modelo.

Con base en los resultados obtenidos en este examen: a. Analice el compromiso (trade-off) entre desempeño y complejidad. b. Determine si incrementar el número de términos lingüísticos produjo una mejora real o únicamente una mayor complejidad. c. Argumente cuál de los tres controladores optimizados utilizaría en una aplicación industrial real. d. Justifique su respuesta utilizando exclusivamente evidencia experimental obtenida durante el examen.

## Nota Importante

La calificación más alta no será obtenida necesariamente por el controlador con el mayor fitness. La calificación más alta será obtenida por el estudiante que demuestre:

- comprensión profunda de la optimización evolutiva;

- comprensión profunda de los sistemas difusos;

- capacidad de análisis crítico;

- interpretación correcta de los resultados experimentales;

- capacidad para justificar decisiones de diseño utilizando evidencia cuantitativa.

Las conclusiones deberán estar respaldadas por resultados experimentales y no por opiniones personales.

---

## Contexto del repositorio OMSDMAG (implementación)

Este repositorio implementa el enunciado anterior. Resumen para agentes:

- **Planta:** `G = lti([0.5], [1, 13.6667, 23.3487, 0])`, simulada con `scipy.signal.lsim`, $T_{sim}=200\\,s$, $x_0=[0,0,0]$, referencia cuadrada $\pm 1$ rad, período 100 s.
- **Universos de discurso:** $e\\in[-\\pi/2,\\pi/2]$, $\\Delta e\\in[-\\pi/6,\\pi/6]$, $v\\in[-8.18,8.18]$.
- **Controladores:** Mamdani con 5/7/9 términos por entrada (`scikit-fuzzy`), optimizados con `pygad` (20 individuos, 30 generaciones, 5 semillas).
- **Módulos clave:** `src/config.py`, `src/plant_sim.py`, `src/fuzzy_controller.py`, `src/chromosome.py`, `src/metrics_fitness.py`, `src/ga_optimizer.py`, `src/plotting_tables.py`.
- **Ejecución:** `python main.py` (o `python main.py --force` para re-ejecutar las 15 corridas). Pruebas: `python -m tests.test_verification`.
- **Documentos relacionados:** `README.md`, `docs/AUDITORIA_PARCIAL2.md`, `docs/CORRECCIONES_PARCIAL2.md`.
- **Artículo de referencia:** `IJFS-D-16-00634_R1.pdf` (Téllez-Velázquez et al., 2017).
