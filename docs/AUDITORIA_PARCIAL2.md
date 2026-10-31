# Auditoría del Parcial 2: hallazgos y plan de correcciones

Documento de seguimiento de la auditoría por micro-segmentos (7 partes) del proyecto
OMSDMAG (controladores Mamdani optimizados con PyGAD, criterio MOTFF).
Sirve como lista de correcciones pendientes. Cada hallazgo tiene un ID para referenciarlo
en commits y en el reporte.

## Alcance y límites de la auditoría

- Se revisó el código de `src/`, `main.py`, `tests/test_verification.py`,
  `build_deliverables.py` (que genera la libreta y el reporte) y los JSON de `results/`.
- **No se ejecutó nada**: el entorno de auditoría no tenía `numpy` ni `scipy`. Lo marcado
  como *(inferido)* sale de leer el código, no de correrlo.
- El texto del artículo (`IJFS-D-16-00634_R1.pdf`) y el del enunciado (`Parcial 2.pdf`) se
  extrajeron con `pdftotext`. El contraste con el enunciado se hizo después de las 7 partes
  de la auditoría; sus consecuencias están en la sección 4 y en los hallazgos H-01, H-08,
  A-01 y A-06, que se ajustaron.
- Las referencias de línea corresponden al estado del repositorio en la rama `revision`
  al momento de la auditoría; pueden desplazarse tras editar.

**Calificación sugerida (revisada tras contrastar con el enunciado): ≈ 74/100.**
La versión inicial era 78/100 (conformidad 31/40, diseño difuso-genético 20/25, análisis
crítico 27/35). Bajó porque H-08 resulta ser una violación explícita del enunciado
("no se aceptará ningún mecanismo de evaluación simplificada"). Además depende de cómo
interprete el profesor el uso de `lsim` dentro de un `for` (H-01). El enunciado aclara que la
nota más alta no la da el mayor fitness sino el análisis crítico con evidencia cuantitativa, así
que conviene priorizar la parte 3 del plan.

---

## Hallazgos críticos (bloqueantes)

> **Atención.** Estos hallazgos incumplen de forma explícita el enunciado, y el propio
> enunciado dice: *"El incumplimiento de cualquiera de las fases invalidará la comparación
> experimental"* y *"Cualquier desviación de estas condiciones invalidará la comparación
> experimental"* (misma función fitness, mismas métricas, mismo simulador). Mientras no se
> corrijan, **los resultados reportados (las 15 corridas, la tabla obligatoria, las figuras y
> las cifras de las 30 respuestas) podrían considerarse inválidos** y deberán regenerarse.

| ID | Qué incumple | Cita del enunciado | Estado |
|---|---|---|---|
| **H-08 (CRÍTICO)** | El GA no evalúa a cada individuo con el controlador real: usa una tabla sustituta de 65×65 (`ga_optimizer.py` L236). La mejor solución se elige con ese fitness. | "No se aceptará ningún mecanismo de evaluación simplificada" (Parte 3, Fase 2) y "Cada individuo deberá evaluarse mediante simulación completa de 200 segundos" | Incumplimiento explícito. Pendiente |
| **H-04 (CRÍTICO)** | El factor q no es la Ec. 13: devuelve `max(\|q_eq13\|, q_span, 1.0)` (`metrics_fitness.py` L50-53). | "Todos los equipos deberán implementar obligatoriamente el factor de penalización" q = (max h⁰ − min hᵢ)/(max h − min h) | Incumplimiento explícito. Pendiente |
| **H-01 (ALTO, riesgo crítico)** | La simulación integra paso a paso con un `for` que llama a `lsim` (`plant_sim.py` L103-127). | "No se permite ... integradores numéricos desarrollados por el estudiante ... métodos de discretización manual" | Ambiguo: el enunciado no explica cómo cerrar el lazo. Pendiente de aclaración con el profesor |

Consecuencias prácticas:
- H-08 y H-04 cambian el fitness de cada individuo, así que la optimización completa debe
  volver a correrse (`python main.py --force`) y hay que regenerar tablas, figuras, libreta y
  reporte.
- Las cifras del análisis (medias, desviaciones, reglas activas, tiempos) cambiarán, y con ellas
  las respuestas que las citan. Conviene corregir el código antes de pulir el análisis.

---

## 1. Matriz de conformidad

| # | Restricción / métrica | Veredicto | Hallazgos |
|---|---|---|---|
| 1 | Planta `lti([0.5],[1,13.6667,23.3487,0])` | Pasa | |
| 2 | Simulación solo con `lsim`, sin `for` paso a paso | **No Pasa (riesgo crítico; enunciado ambiguo)** | H-01, H-02 |
| 3 | Referencia ±1 rad, T = 100 s, 200 s, sin ruido | Pasa (alerta) | H-03 |
| 4 | Universos `[-π/2, π/2]`, `[-π/6, π/6]`, `[-8.18, 8.18]` | Pasa (alerta) | H-07, H-09 |
| 5 | Universos inmutables | Pasa | |
| 6 | Soporte para 5/7/9 términos | Pasa | |
| 7 | Triangulares con `a<b<c`, centros en rango, traslape > 0 | Pasa (alerta) | H-10, H-11, H-12 |
| 8 | Genes de supresión de reglas | Pasa | H-14 |
| 9 | Número de reglas no estático | Pasa | |
| 10 | 8 objetivos (semiciclo positivo y negativo) | Pasa (alerta) | H-05 |
| 11 | OS en %, SSE en rad, tr/ts en s | Pasa | |
| 12 | `tr0 = 9`, `ts0 = 13` | Pasa (alerta) | H-06 |
| 13 | Factor q = (max h⁰ − min hᵢ)/(max h − min h) | **No Pasa (CRÍTICO)** | H-04 |
| 14 | Población ≥ 20 y generaciones ≥ 30 | Pasa (en el mínimo) | H-15 |
| 15 | ≥ 5 semillas independientes | Pasa | |
| 16 | Análisis crítico | Parcial / **No Pasa** (supresión) | A-01 a A-08 |
| 17 | Evaluación de cada individuo sin mecanismo simplificado (enunciado, Parte 3, Fase 2) | **No Pasa (CRÍTICO)** | H-08, N-06 |
| 18 | Pesos w1..w8 con justificación técnica (enunciado, Parte 2) | Parcial | N-01 |
| 19 | Paso temporal justificado si difiere del ejemplo `dt = 0.01` | Parcial | N-02 |
| 20 | Estructura obligatoria del reporte (5 secciones) | Parcial | N-03 |

---

## 2. Hallazgos de código

Severidad: **CRÍTICA** = incumple de forma explícita una restricción obligatoria del enunciado
y puede invalidar los resultados; **Alta** = incumplimiento probable o riesgo de invalidación
pendiente de aclarar; **Media** = afecta la validez de los resultados; **Baja** = diseño
mejorable.

### H-01 (Alta, riesgo crítico): lazo `for` que integra paso a paso con `lsim`
- **Dónde:** `src/plant_sim.py` L103-127.
- **Qué pasa:** `simulate()` recorre 2001 muestras y llama a `lsim` en cada intervalo
  `[0, dt]` con `X0` igual al estado actual. No hay `odeint` ni `solve_ivp`, pero el criterio
  "ciclos for integrando paso a paso" se cumple al pie de la letra.
- **Contraste con el enunciado:** `Parcial 2.pdf` prohíbe "integradores numéricos
  desarrollados por el estudiante" y "métodos de discretización manual", y pide la respuesta
  "exclusivamente mediante `lsim(G, U=u, T=t, X0=x0)`". El propio enunciado no explica cómo
  cerrar el lazo con `u` generado por el controlador, y aclara que su código base "NO
  resuelve el examen". Es una ambigüedad real: conviene preguntarle al profesor y dejar la
  respuesta por escrito.
- **Corrección propuesta:** decidir y documentar una de dos vías:
  1. Consultar con el profesor si el lazo con `lsim` por paso es aceptable para un
     controlador no lineal en lazo cerrado (una sola llamada a `lsim` no puede cerrar el lazo).
  2. Si no es aceptable, justificar explícitamente en el reporte por qué el lazo cerrado con
     controlador difuso exige evaluar `u[k]` en cada instante, y mantener la llamada final
     `lsim(G, U=u, T=t, X0=x0)` como verificación.

### H-02 (Media): ZOH en el lazo, interpolación lineal en el `lsim` final *(inferido)*
- **Dónde:** `plant_sim.py` L123 (`interp=False`) frente a L130 (`lsim` por defecto).
- **Qué pasa:** la respuesta que se evalúa (`theta` del `lsim` final) no es exactamente la
  del lazo que decidió `u`.
- **Corrección propuesta:** usar el mismo modo de interpolación en ambos sitios, o evaluar las
  métricas sobre el `theta` del lazo. Añadir un test que compare ambas trayectorias.
  Nota: `interp` está deprecado en versiones recientes de SciPy; verificar la versión instalada.

### H-03 (Baja): muestra final manipulada a mano
- **Dónde:** `plant_sim.py` L46-47 (`r[-1] = -1.0`).
- **Qué pasa:** en t = 200 s una onda cuadrada pura valdría +1; se fuerza −1.
- **Corrección propuesta:** quitar el parche, o documentar que se define la referencia en
  `[0, 200)` y se mantiene el valor del último semiperiodo en el instante final.

### H-04 (CRÍTICA): el factor q no es la Ec. 13
- **Dónde:** `src/metrics_fitness.py` L50-53.
- **Qué pasa:** se calcula `q_eq13` literal, pero se devuelve
  `max(|q_eq13|, q_span, 1.0)` con `q_span = (max h0 − min h0)/(max h − min h)`. Si
  `min(h) ≥ -1`, que es lo habitual, `q_span ≥ q_eq13`, así que el q efectivo es 2/rango.
  Ejemplo: h ∈ [-0.5, 0.5] → Ec. 13 = 1.5, código = 2.0.
- **Corrección propuesta:** `return max(q_eq13, 1.0)` (el piso en 1 es defendible porque el
  artículo aplica q solo si `[min h, max h] ⊆ [min h0, max h0]`). Actualizar los tests de
  `tests/test_verification.py` y regenerar resultados. Corregir Q12 del reporte si cambia
  la redacción.

### H-05 (Media): q por ventana y métricas negativas promediadas antes de f
- **Dónde:** `metrics_fitness.py` L95-97 y L213-230.
- **Qué pasa:** el artículo define h sobre toda la simulación; aquí se usa cada ventana. Para
  el semiciclo negativo se promedian OS, SSE, tr, ts y q de dos ventanas y luego se aplican
  las funciones no lineales f5–f8, lo que no equivale a promediar f.
- **Corrección propuesta:** calcular f de cada ventana negativa y promediar las f; decidir y
  documentar si q usa h de toda la simulación.

### H-06 (Baja): `tr0` y `ts0` sobrescribibles
- **Dónde:** `evaluate_controller_response(..., tr0=TR0, ts0=TS0)`.
- **Corrección propuesta:** leer `TR0` y `TS0` directamente de `config.py`, sin argumentos.

### H-07 (Media): universo de voltaje truncado en el fitness del GA *(inferido)*
- **Dónde:** `src/fuzzy_controller.py` L204-205 (`voltage_universe[::4]`).
- **Qué pasa:** el centroide de la tabla de búsqueda usa 250 puntos que llegan a ≈ +8.13 V,
  no a +8.18 V, y con menor resolución que la evaluación final.
- **Corrección propuesta:** muestrear incluyendo el extremo (por ejemplo `np.linspace`
  sobre el mismo universo o `[::4]` más el último punto).

### H-08 (CRÍTICA): el GA optimiza una tabla sustituta, no el controlador exacto
- **Dónde:** `src/ga_optimizer.py` L236 (tabla 65×65) y L243 (resta `repair_penalty`).
- **Qué pasa:** `fitness_ga_lookup` y `fitness_exact` difieren hasta ≈ 0.06 en los JSON
  (9 términos, semilla 777: 0.6721 contra 0.7327; 5 términos, semilla 100: 0.7097 contra
  0.7554). La mejor solución se elige con el fitness sustituto y la penalización solo se
  resta en el GA.
- **Contraste con el enunciado (Parte 3, Fase 2):** "Cada individuo deberá evaluarse mediante
  simulación completa de 200 segundos ... No se aceptará ningún mecanismo de evaluación
  simplificada." Y en la Fase 3, el mejor individuo se selecciona "utilizando exclusivamente la
  función fitness definida". La tabla 65×65 es una evaluación simplificada, así que esto es una
  violación explícita, no solo una limitación de validez. Corrige lo dictaminado en la Parte 6,
  donde se clasificó como alerta menor.
- **Corrección propuesta:** evaluar cada individuo con la inferencia exacta (`compute_crisp`
  o `skfuzzy.control`) dentro de `fitness_func`. Si el costo es inaceptable, aceptar menos
  generaciones no es opción (mínimo 30), así que hay que optimizar la inferencia exacta
  (vectorizar, reducir la malla de 1000 puntos si se justifica) y no sustituirla. Reportar
  fitness exacto y penalización por separado.

### H-09 (Media): saturación de `e` y `Δe` en las entradas
- **Dónde:** `plant_sim.py` L109-110.
- **Qué pasa:** |e| llega a 2 rad en cada conmutación pero se recorta a ±π/2; |Δe| se
  recorta a ±π/6. Es saturación, no reescalado, pero se pierde información justo en el
  régimen que fija el tiempo de subida.
- **Corrección propuesta:** documentar la saturación en el reporte como decisión de
  diseño y analizar su efecto sobre `tr` (por ejemplo contando cuántas muestras saturan).

### H-10 (Baja): genes inertes
- **Dónde:** `src/chromosome.py` L146-147 y L171-180.
- **Qué pasa:** los centros extremos quedan anclados (`u_min + du`, `u_max − du`) y
  `w_left[0]` y `w_right[N-1]` no se usan: 4 genes inertes por variable, 12 por cromosoma. El
  GA no define esos centros y los triángulos extremos son casi hombros.
- **Corrección propuesta:** eliminar esos genes del cromosoma, o dejarlos evolucionar y
  documentar la decisión. Ajustar `get_num_genes` y los tests (95/161/243).

### H-11 (Baja): traslape mínimo casi nulo y sin penalización
- **Dónde:** `chromosome.py` L197-204.
- **Qué pasa:** la reparación puede dejar `c_k − a_{k+1} = 0.5·du` (≈ 0.0016 rad en `error`):
  formalmente positivo pero casi una partición nítida. No se penaliza.
- **Corrección propuesta:** exigir un traslape mínimo relativo (por ejemplo un porcentaje del
  ancho) y penalizar cuando se necesite reparar.

### H-12 (Baja): reparación por `sort` sin reescribir el gen
- **Dónde:** `chromosome.py` L135-144.
- **Qué pasa:** hay redundancia genotipo-fenotipo (muchos cromosomas decodifican igual) y la
  penalización de 0.02 por centros desordenados casi siempre se aplica, así que no guía la
  búsqueda. Se resta en `ga_optimizer.py` L243.
- **Corrección propuesta:** codificar los centros como incrementos positivos acumulados, o
  reescribir en el cromosoma el valor reparado (reparación lamarckiana).

### H-13 (Media): zonas sin regla disparada devuelven 0 V *(inferido)*
- **Dónde:** `fuzzy_controller.py` L152-153.
- **Qué pasa:** si ninguna regla dispara, `compute_crisp` devuelve 0.0. Al suprimir reglas
  pueden aparecer zonas muertas silenciosas. No hay chequeo de completitud de la base de
  reglas.
- **Corrección propuesta:** medir la cobertura (fracción de la malla `(e, Δe)` sin regla
  disparada) para cada controlador final y penalizarla o reportarla.

### H-14 (Baja): sesgo hacia más reglas en la búsqueda
- **Dónde:** `ga_optimizer.py` L103-113 (población inicial con 55–95 % de reglas activas y
  la regla central fija en 0.95) y L262-264 (`mutation_by_replacement=False`, pasos de ±0.25).
- **Qué pasa:** con umbral 0.5, un gen en 0.9 difícilmente se apaga por mutación; se apaga
  sobre todo por cruza o selección. No hay término de parsimonia en el fitness.
- **Corrección propuesta:** inicializar con tasas de activación más amplias, mutar los genes
  de activación por volteo o reemplazo, y valorar un término de parsimonia.

### H-15 (Baja): configuración en el mínimo exacto y resultados en caché
- **Dónde:** `config.py` L61-62; `ga_optimizer.py` L209-211.
- **Qué pasa:** 20 individuos y 30 generaciones es justo el mínimo. Con `force_rerun=False`,
  si existe `results/runs/*.json` se devuelven esos resultados sin volver a ejecutar.
- **Corrección propuesta:** usar `--force` (ver README) al validar cambios; valorar más
  generaciones si el tiempo lo permite.

---

## 3. Hallazgos del análisis crítico (reporte y libreta)

El texto del reporte se genera en `build_deliverables.py` (`build_30_questions_markdown`).
Corregir allí y regenerar la libreta y el DOCX (ver README, sección 3).

### A-01: Q1 y Q23 no contrastan la premisa del enunciado con lo medido
- El "10×" (Q1) y el "8×" (Q23) son premisas hipotéticas del propio enunciado ("Suponga
  ..."), así que citarlas no es un error.
- **Medido:** 169.63 → 172.32 → 181.87 s (×1.07 de 5 a 9 términos). La respuesta debe
  contestar la hipótesis y decir explícitamente que en los experimentos propios el sobrecosto de
  optimización es solo ×1.07.
- Falta explicar por qué casi no crece con N: el fitness usa una tabla 65×65 y el costo lo
  domina el lazo de `lsim`, que no depende de N. Ojo: si se corrige H-08, este tiempo
  cambiará y habrá que reescribir la discusión con los nuevos valores.
- **Acción:** añadir el contraste con el valor medido y la causa.

### A-02: sin prueba estadística y contradicción entre Q2 y Q23
- n = 5 corridas por configuración y σ ≈ 0.05–0.06.
  Fitness medio: 0.7218 ± 0.0488 (5), 0.7299 ± 0.0593 (7), 0.7134 ± 0.0649 (9).
- Q2 dice que con 9 términos el desempeño "cae"; Q23 dice que la diferencia no es
  significativa.
- La explicación de "dilución de la búsqueda" (Q2, Q3) no está contrastada.
- **Acción:** añadir Mann-Whitney o intervalos de confianza; unificar Q2 y Q23; presentar la
  dilución como hipótesis.

### A-03: la supresión de reglas no sigue el patrón que se afirma
Probabilidad de regla activa según la distancia al centro, pooled sobre las 5 semillas
(calculada desde `decoded_mfs.rule_active` en `results/runs/*.json`):

| Términos | Distancia al centro, índice de `error` | Distancia al centro, índice de `derror` |
|---|---|---|
| 5 | 0: 0.68, 1: 0.62, 2: 0.78 | 0: 0.80, 1: 0.68, 2: 0.66 |
| 7 | 0: 0.63, 1: 0.71, 2: 0.81, 3: 0.71 | 0: 0.91, 1: 0.69, 2: 0.74, 3: 0.67 |
| 9 | 0: 0.78, 1: 0.64, 2: 0.62, 3: 0.72, 4: 0.64 | 0: 0.84, 1: 0.61, 2: 0.57, 3: 0.67, 4: 0.76 |

- Las reglas de error grande no se suprimen más que las centrales; solo destaca la columna
  `derror = ZE` (80–91 %).
- Fracción de reglas activas casi constante: 17.4/25, 35.8/49 y 54.4/81 (≈ 67–73 %).
- Spearman número de reglas contra fitness exacto: −0.1 (5), 0.5 (7), 0.3 (9); pooled 0.23.
- **Acción:** reportar estas cifras, quitar o matizar la narrativa de "reglas finas
  permanecen, reglas de error grande se suprimen", y explicar la fracción constante.

### A-04: contradicción entre Q7 y Q13
- Q7 afirma que las combinaciones extremas "nunca se visitan".
- Q13 admite que |e| llega a ±2 rad en cada conmutación (saturando el universo).
- **Acción:** corregir Q7 (la región de error grande sí se visita en cada transición) y
  alinear Q16, que también supone un "corredor" no visitado.

### A-05: falta ablación regla por regla
- Sin ella, las celdas apagadas pueden ser deriva neutral o sesgo de la inicialización
  (H-14), no efecto de selección.
- Q6 atribuye a la poda la mejora de `tr` frente al baseline, pero el GA cambió a la vez las
  funciones de membresía y los consecuentes (confusión de factores).
- **Acción:** para el mejor controlador de cada N, reactivar o desactivar cada regla de una
  en una y medir el cambio en fitness y en las métricas (como la Tabla 11 del artículo).
  Distinguir reglas neutras, útiles y perjudiciales.

### A-06: MOTFF contra RMSE sin experimento propio
- Q11 se apoya en la Tabla 13 del artículo (caso con 50 % de ruido), no en un experimento
  propio.
- En este código el `tr` ya se normaliza con `r_init` y `r_final` (`metrics_fitness.py`
  L92) y exige cruzar el 90 %, así que un falso `tr` da `tr = 50 s` aun sin q. Los q > 1
  casi solo aparecen en corridas fallidas (9 términos, semilla 777: q = 1.165, tr = 50 s).
- La necesidad de q no está demostrada.
- El enunciado (Parte 5) exige que las respuestas se apoyen en "resultados obtenidos durante
  el examen" y no en opiniones; la Q30(d) pide "exclusivamente evidencia experimental obtenida
  durante el examen". Citar la Tabla 13 del artículo en Q11 no cumple eso.
- **Acción:** correr el GA con MOTFF sin q y con RMSE y comparar. Llamar al fenómeno
  "explotación de la métrica", no sobreajuste.

### A-07: Q4 y Q5 (reglas y parsimonia)
- Q5 compara baseline (100 % de reglas, funciones de membresía `automf`) con optimizados y
  concluye que más reglas no implica mejor control: confunde el efecto del número de
  reglas con el de las funciones de membresía. Los datos tampoco muestran correlación
  negativa (A-03).
- Q4 incluye la afirmación "menor riesgo de sobreajuste" sin evidencia.
- **Acción:** sustentar con la ablación (A-05) y el análisis estadístico (A-02).

### A-08: Q12 cita la Ec. 13 literal y el código usa otra
- **Acción:** tras corregir H-04, comprobar que Q12 y los valores citados
  (`q⁺ ≈ 1.000–1.007`, `q⁻ ≈ 1.000–1.006`) coincidan con los resultados regenerados.

### Aciertos a conservar
- Espacio discreto de reglas `(N+1)^(N²)` correcto (≈ 2.84·10¹⁹, 1.8·10⁴⁴, 10⁸¹).
- Costos medidos de inferencia (10.07 → 22.76 → 36.59 ms, 3.63×) y memoria
  (0.49 → 1.44 MB) bien reportados.
- Pruebas de cromosomas aleatorios en `tests/test_verification.py` para `a<b<c` y traslape.

---

## 4. Contraste con `Parcial 2.pdf`

Lo que el enunciado exige y cómo queda frente a los hallazgos.

### Confirma o endurece hallazgos previos
- **H-04 (q):** el enunciado dice "deberán implementar obligatoriamente" q = (max h⁰ − min hᵢ)/
  (max h − min h). La implementación actual no es esa fórmula. Se mantiene como No Pasa. Los
  tests existentes no lo detectan: `test_equations_12_and_13` (L103-105) usa un caso con
  `min(h) = -1`, donde ambas expresiones coinciden (q = 4.0).
- **H-06:** "tr0 = 9 s y ts0 = 13 s no podrán modificarse, optimizarse ni ajustarse
  manualmente": reforzar quitando los argumentos sobrescribibles.
- **H-08:** pasa de Media a Alta (ver arriba).
- **A-02, A-05, A-06:** el enunciado dice que la nota más alta se da por "comprensión
  profunda", "análisis crítico" y "conclusiones respaldadas por resultados experimentales".
  Q11 con la Tabla 13 del artículo no cumple "resultados obtenidos durante el examen".

### Hallazgos nuevos a partir del enunciado
- **N-01 (pesos):** el enunciado pide que los pesos "deberán justificarse técnicamente". El
  reporte los declara iguales (0.125) pero no da una justificación propia (el artículo los
  iguala para dar la misma importancia a las 8 medidas). *Acción:* añadir un párrafo de
  justificación en Metodología (`build_deliverables.py`, sección de la función fitness).
- **N-02 (paso temporal):** el ejemplo del enunciado usa `dt = 0.01`; se permite cambiarlo
  "siempre que se justifique técnicamente". El proyecto usa `DT = 0.10` (10× más grueso) y no
  encontré una justificación. Afecta la resolución de `tr`/`ts` (0.1 s) y `Δe` por diferencias
  finitas. *Acción:* justificar (costo del GA, resolución necesaria) y, si es viable, evaluar
  la sensibilidad a `DT` en el mejor controlador.
- **N-03 (estructura del reporte):** el enunciado exige 1 Introducción, 2 Metodología,
  3 Resultados, 4 Discusión, 5 Conclusiones. La libreta usa otra numeración y junta
  Discusión y Conclusiones en "8". La Discusión obligatoria incluye "robustez de las
  soluciones" y Resultados incluye "análisis estadístico de las cinco ejecuciones" (A-02).
  *Acción:* alinear títulos y verificar que cada ítem obligatorio tenga su sección.
- **N-04 (reglas en la tabla):** la tabla obligatoria muestra el conteo (`16 / 25`). Las
  reglas exactas sí se listan después (libreta 6.1 y sección del DOCX), así que cumple, pero
  conviene referenciar ese listado desde la fila "Reglas activas" de la tabla.
- **N-05 (documentación obsoleta):** `fuzzy_controller.py` (docstring de
  `build_lookup_control_law`) habla de "4,001 muestras", pero con `DT = 0.10` son 2001.
  Quedará sin efecto si se elimina la tabla (H-08).
- **N-06 (selección del mejor individuo):** hoy `best_solution()` de PyGAD elige con el
  fitness de la tabla sustituta. El enunciado pide seleccionar con la función fitness
  definida (Fase 3). Se resuelve con H-08.
- **N-07 (inferencia propia en lugar de `skfuzzy.control`):** el enunciado lista
  `skfuzzy.control` como biblioteca obligatoria y manda "construir el sistema difuso" en el
  fitness. La simulación y el fitness usan una inferencia propia (`compute_crisp` o la tabla);
  `skfuzzy.control` solo se usa para medir el tiempo y para un test. Ese test
  (`test_skfuzzy_equivalence`) solo cubre los controladores `automf` (no los optimizados) y
  entradas dentro del 95 % del rango. *Acción:* ampliar el test a cromosomas optimizados y a
  todo el rango, o evaluar el fitness con `skfuzzy.control` si el costo lo permite.

### Lo que el enunciado confirma como correcto
Planta con `lti`/`lsim`, `square`, `x0 = [0,0,0]`, universos fijos, baselines con `automf`,
`pygad` exclusivo, mínimo 20 individuos y 30 generaciones, 5 semillas con media y
desviación estándar, tiempo de inferencia con `perf_counter()` sobre `controller.compute()`,
tiempo de optimización con `time.time()`, 8 métricas, pesos que suman 1, `tr0/ts0` usados y la
salida de reglas activas por individuo.

---

## 5. Plan de correcciones priorizado

- [ ] **P0 (CRÍTICO, bloqueante)** H-04: corregir q a `max(q_eq13, 1.0)`; actualizar tests y
      regenerar. Ampliar el test de q con un caso donde `min(h) > -1`.
- [ ] **P1** H-01 / H-02: decidir el tratamiento del lazo con `lsim` y alinear la interpolación.
- [ ] **P1** A-01 / A-02: corregir "10×" y "8×"; añadir prueba estadística; reconciliar Q2 y Q23.
- [ ] **P1** A-03 / A-04 / A-05: reescribir el análisis de supresión con los datos reales y
      hacer la ablación regla por regla.
- [ ] **P0 (CRÍTICO, bloqueante)** H-08 / N-06: evaluar cada individuo con la inferencia exacta
      (violación explícita del enunciado); seleccionar el mejor con ese fitness; reportar la
      penalización aparte. Después de P0, volver a correr todo (`python main.py --force`).
- [ ] **P1** N-01 / N-02 / N-03: justificar pesos y `DT`; alinear la estructura del reporte.
- [ ] **P2** H-05 / H-07 / H-13: promedio de f, universo de voltaje completo, cobertura de reglas.
- [ ] **P2** A-06: experimento propio MOTFF sin q y con RMSE.
- [ ] **P2** N-07: ampliar `test_skfuzzy_equivalence` a cromosomas optimizados y todo el rango.
- [ ] **P3** H-03, H-06, H-09 a H-12, H-14, H-15, N-04, N-05: ajustes de diseño y documentación.
- [ ] Regenerar tablas, figuras, libreta y reporte
      (`python main.py`, luego `python build_deliverables.py`) y volver a ejecutar
      `python -m tests.test_verification`.
