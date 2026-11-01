# Documentación de anomalías, inconsistencias y correcciones (nueva versión)

Registro de las anomalías e inconsistencias detectadas en el código original del proyecto
(ahora **archivado sin modificar en `codigo de cristian/`**) y de las correcciones
aplicadas en la nueva versión (`src/`, `main.py`, `tests/`), contrastadas con el enunciado
oficial `Parcial 2.pdf` (Partes 1–5).

Los identificadores **H-xx** (hallazgos de código), **A-xx** (análisis) y **N-xx** (nuevos
tras contrastar con el enunciado) provienen de `docs/AUDITORIA_PARCIAL2.md`, que es el
insumo de esta revisión.

---

## 1. Alcance y método

- **Base normativa:** `Parcial 2.pdf` (Partes 1–5: planta/lsim, fitness y Ec. (13),
  protocolo experimental de 5 fases, código base, preguntas de análisis).
- **Base de auditoría:** `docs/AUDITORIA_PARCIAL2.md` (matriz de conformidad + hallazgos).
- **Principio de trazabilidad:** cada corrección se ancla a la cláusula literal del
  enunciado que la exige, incluye código antes/después, y queda protegida por una prueba
  unitaria que impide la regresión.
- **Código original inalterado:** todo el proyecto viejo se movió intacto a
  `codigo de cristian/`; la nueva versión se construyó de cero en la raíz partiendo de esa
  base, sin sobrescribir el archivado.

---

## 2. Resumen ejecutivo de anomalías corregidas

| ID | Severidad | Anomalía (estado original) | Cláusula del enunciado incumplida | Corrección aplicada | Test que la protege |
|---|---|---|---|---|---|
| **H-08** | CRÍTICA (bloqueante) | El GA evaluaba cada individuo con una **tabla sustituta 65×65** (`build_lookup_control_law`), no con el controlador real. La penalización de reparación se **restaba al fitness** (L243 del original). | "Cada individuo deberá evaluarse mediante simulación completa de 200 segundos… **No se aceptará ningún mecanismo de evaluación simplificada**" (Parte 3, Fase 2); "La selección deberá realizarse utilizando exclusivamente la función fitness definida" (Fase 3) | Fitness evalúa con inferencia Mamdani **exacta** (`compute_crisp`) + simulación completa de 200 s; tabla eliminada por completo; `repair_penalty` reportada **aparte**, sin mezclarse | `test_ga_uses_exact_inference` |
| **H-04** | CRÍTICA (bloqueante) | El factor q no era la Ec. (13): devolvía `max(abs(q_eq13), q_span, 1.0)` con un término inventado `q_span`. Con `h ∈ [-0.5, 0.5]` daba **2.0** en lugar de **1.5**. | "Todos los equipos deberán implementar obligatoriamente el factor de penalización q = (max(h0) − min(hi)) / (max(h) − min(h))" (Parte 2, Ec. 13) | `q = max((max(h0) − min(h)) / (max(h) − min(h)), 1.0)`, literal y con el piso justificado; `q_span` eliminado | `test_equations_12_and_13` (caso `min(h) > −1`) |
| **H-02** | MEDIA | El lazo integraba con ZOH (`interp=False`, paso a paso) pero el `lsim` final de 200 s usaba **interpolación lineal** (`interp=True` por defecto): la trayectoria evaluada en métricas no era la que decidió `u`. | "La respuesta temporal deberá obtenerse mediante `lsim(G, U=u, T=t, X0=x0)`" (Parte 1) y "las mismas… métricas de evaluación… el mismo simulador" (Nota Metodológica) | `lsim` final con `interp=False` (mismo ZOH que el lazo). El error de consistencia lazo/global ahora se calcula y se exige `≈ 0` | `test_plant_and_reference` (consistencia `< 1e-9`) |
| **H-03** | BAJA | Muestra final manipulada a mano: `r[-1] = -1.0` parchado tras `square()`. | Definición de la referencia cuadrada ±1 rad, período 100 s, ciclo útil 50 % (Parte 1) | Referencia **definida explícitamente por semiperíodos** sobre `[0, 200] s`; `t = 200` pertenece al semiperíodo `[150, 200]` (= −1) por construcción, no por parche | `test_plant_and_reference` (`r[-1] == -1` + signos por semiperíodo) |
| **H-05** | MEDIA | En el semiciclo negativo se promediaban **métricas** (OS, SSE, tr, ts, q) y después se aplicaban las funciones no lineales `f5–f8`, lo que no equivale a promediar `f`. | "La función fitness deberá implementarse obligatoriamente como [Ec. 12]" (Parte 2) — las 8 contribuciones se computan por transición y la Ec. 12 es lineal en `f`, no en métricas | Se calculan `f5–f8` de **cada ventana negativa** y se promedian las **contribuciones**; el promedio de métricas se conserva solo para el reporte | `test_equations_12_and_13` (verifica la forma exacta de la Ec. 12) |
| **H-06** | BAJA | `evaluate_controller_response(..., tr0=TR0, ts0=TS0)`: `tr0`/`ts0` sobre­escribibles por argumento. | "Estos valores no podrán modificarse, optimizarse ni ajustarse manualmente. Su modificación invalidará los resultados" (Parte 2, Constantes Obligatorias) | Los argumentos **se eliminaron**; los valores se leen fijos desde `src/config.py` | `test_equations_12_and_13` (firma sin `tr0`/`ts0`) |
| **N-07-derivado** | MEDIA (detectada por tests) | La inferencia "exacta" `compute_crisp` **no coincidía exactamente** con `skfuzzy.control.controller.compute()`: hasta **≈ 0.0037 V** de diferencia en cromosomas optimizados, porque defuzzificaba sobre la malla uniforme de 1000 puntos sin el remuestreo en puntos de cruce que hace scikit-fuzzy. | La libreta/report afirmaban equivalencia exacta; el enunciado obliga a `skfuzzy`/`skfuzzy.control` (Parte 4, Bibliotecas Obligatorias) | `compute_crisp` replica el procedimiento interno de `CrispValueCalculator.find_memberships` (`_interp_universe_fast` + `np.union1d` + `interp_membership` + defuzz centroide), con equivalencia de máquina | `test_skfuzzy_equivalence` extendida (automf + optimizados + reparados, rango completo) |

---

## 3. Detalle de las correcciones críticas

### 3.1 H-08 — evaluación simplificada en el GA (CRÍTICA)

**Qué hacía el código original** (`codigo de cristian/src/ga_optimizer.py`, L236 y L243):

```python
# ORIGINAL (archivado)
law = ctrl_fast.build_lookup_control_law(grid_size=65)   # tabla sustituta 65x65
sim_out = simulator.simulate(law)
fit_val = float(res["fitness"]) - float(ctrl_fast.decoded["repair_penalty"])  # mezcla
```

Evidencia empírica de la auditoría: en los JSON viejos `fitness_ga_lookup` y
`fitness_exact` diferían hasta **≈ 0.06** (p. ej. 9 términos, semilla 777: 0.6721 vs
0.7327). Es decir, PyGAD ordenaba y elegía individuos con otra función distinta a la
Ec. (12).

**Qué hace la nueva versión** (`src/ga_optimizer.py`):

```python
# NUEVO: cada individuo se evalúa con la inferencia Mamdani EXACTA y los 200 s completos
sim_out = simulator.simulate(ctrl_fast.compute_crisp)
res = evaluate_controller_response(sim_out["t"], sim_out["theta"])
fitness_eval = float(res["fitness"])
```

Decisiones explícitas plasmadas en el código y en el JSON:

1. **`build_lookup_control_law` fue eliminada** (no "aislada"): no existe en la nueva
   versión y un test impide reintroducirla, porque el enunciado prohíbe
   *"cualquier mecanismo de evaluación simplificada"*.
2. **Selección exclusivamente por la función fitness definida:** `best_solution()` de
   PyGAD ya opera sobre `fitness_func`, y `fitness_func` devuelve únicamente la Ec. (12)
   exacta; por eso **la penalización de reparación NO se resta, escala ni mezcla**.
   La combinación está documentada en un bloque de comentario sobre `fitness_func`
   ("CÓMO SE COMBINAN EL FITNESS EXACTO Y LA PENALIZACIÓN DE REPARACIÓN").
3. **Reporte separado por individuo ganador** — campos nuevos del JSON:
   - `fitness_ga`: fitness exacto con el que PyGAD eligió,
   - `fitness_exact`: re-evaluación final del mejor cromosoma reconstruido con grafo
     `skfuzzy.control`,
   - `fitness_gap`: `fitness_exact − fitness_ga` (auditable; idealmente ≈ 0),
   - `repair_penalty`: magnitud de reparaciones ≥ 0 **sin efecto sobre el fitness**,
   - `penalty_handling`: texto explicativo legible dentro del JSON.
   - `lsim_consistency_error`: `max |theta(eval) − theta(lazo)|`, debe ser ≈ 0.
4. **Costo computacional, sin cambiar la semántica** (medido antes de pausar la
   ejecución: ~1.0–1.4 s por simulación completa de 200 s con inferencia exacta):
   - No se reconstruye `ControlSystem`/`ControlSystemSimulation` por individuo:
     el fitness usa `build_control_system_graph=False` y solo arreglos numpy.
   - La inferencia exacta usa activaciones vectorizadas con numpy
     (`firing_matrix = min(mu_e[:,None], mu_de[None,:])`).
   - El grafo completo de `skfuzzy.control` se construye **solo** en la evaluación
     final (Fase 3) y para medir `controller.compute()` con `perf_counter()`
     (pág. 14 del enunciado).
   - No se redujo población (20) ni generaciones (30).

### 3.2 H-04 — factor q literal de la Ec. (13) (CRÍTICA)

**Original:** `return float(max(abs(q_eq13), q_span, 1.0))` — con `q_span =
(max(h0) − min(h0)) / (max(h) − min(h))`, término que no existe en la Ec. (13). Con
`h ∈ [-0.5, 0.5]` la Ec. (13) da `(1−(−0.5))/1 = 1.5`, pero el código viejo daba `2.0`.

**Nuevo:** `src/metrics_fitness.py`:

```python
q_eq13 = (float(h0_max) - h_min) / denom
return float(max(q_eq13, 1.0))
```

**Decisión documentada (dentro del docstring de `compute_penalty_factor_q`):**

- `h` se toma **por ventana de transición**: es exactamente el caso que el artículo cita
  como motivación del factor (*"...prevents rating with a good score all the very short
  and incorrect rise times, when the steady state is reached under the reference
  value"*); un único `h` global enmascararía ese caso entre las demás transiciones.
- El `h0` de la ventana es `{r_init, r_final} ⊂ {−1, +1} rad`, así que `max(h0) = 1.0`
  en ambas direcciones y **numéricamente coincide** con el `h0` de toda la simulación
  (la referencia global vive solo en `[−1, +1]`).
- **Piso `q ≥ 1.0`:** el artículo solo penaliza cuando `[min(h), max(h)] ⊆
  [min(h0), max(h0)]`; con sobreimpulso recorridos mayores al de la referencia no deben
  *bonificarse* con un `q < 1`.

Los tests antiguos que siguen siendo válidos se conservaron (q = 4.0 con
`h ∈ [−1, −0.5]`, respuesta plana con `q ≥ 1e5`, OS en porcentaje, respuesta ideal con
tr=9/ts=13); el nuevo test distingue la Ec. 13 del código anterior:

```python
h_centered = np.linspace(-0.5, 0.5, 100)
q_centered = compute_penalty_factor_q(h_centered, h0_min=-1.0, h0_max=1.0)
assert np.isclose(q_centered, 1.5, atol=1e-9)   # el código viejo daba 2.0
```

---

## 4. Detalle de las correcciones de simulación y fitness

### 4.1 H-02 — interpolación consistente entre lazo y `lsim` global

El lazo no lineal requiere decidir `u[k]` antes de integrar `[t_k, t_{k+1})`; por eso la
unidad de propagación de estado es `lsim` por intervalo con entrada constante (ZOH,
`interp=False`). El error era dejar la verificación global con `interp=True`
(interpolación lineal), lo que producía una trayectoria evaluada distinta de la generada
por la ley de control (diferencias del orden de 4.5e−3 rad en bits previos).

**Nuevo** (`src/plant_sim.py`):

```python
tout, theta, xout = lsim(self.G, U=u, T=self.t, X0=self.x0, interp=False)
```

Además, `simulate()` retorna `theta_loop` (trayectoria del lazo) y
`lsim_consistency_error = max |theta − theta_loop|`, verificado en `0.00e+00` en la
última corrida antes de pausar la ejecución.

**Nota sobre H-01 (Alta, pendiente de aclarar con el profesor):** el lazo paso a paso con
`lsim` es la única forma de cerrarlo con un controlador no lineal (el `u` de cada
intervalo no se conoce de antemano); se mantiene la llamada global obligatoria
`lsim(G, U=u, T=t, X0=x0)` como verificación. **Acción pendiente:** confirmar con el
profesor si este cierre es aceptable y documentar la respuesta en el reporte (el
hallazgo queda abierto; sí quedó documentada la justificación técnica en el docstring de
`ClosedLoopPlantSimulator`).

### 4.2 H-03 — referencia cuadrada definida por construcción

Se sustituye `square()` + parche `r[-1] = -1.0` por una definición explícita por
semiperíodos sobre `[0, 200] s`:

```text
[0, 50) s → +1 | [50, 100) s → −1 | [100, 150) s → +1 | [150, 200] s → −1
```

El enunciado exige *señal cuadrada ±1 rad, período 100 s, ciclo útil 50 %* y que cambie
de signo cada 50 s; con la definición explícita, el instante final `t = 200` pertenece al
semiperíodo `[150, 200]` (= −1) por construcción y no hay muestra artificial con salto de
+2 rad.

### 4.3 H-05 — promedio de contribuciones `f`, no de métricas

Original: promediaba `OS, SSE, tr, ts, q` de las dos ventanas negativas y luego aplicaba
`f5–f8`. Como `f` no son lineales, esa vía no respeta la Ec. (12). Nuevo
(`_fitness_components` + `evaluate_controller_response`): se calculan `f5–f8` por
ventana y se promedian **las contribuciones**; el promedio de métricas se conserva solo
como valor de reporte.

### 4.4 H-06 — `tr0`/`ts0` inmutables

Firma nueva: `evaluate_controller_response(t, theta, weights=FITNESS_WEIGHTS)` — sin
`tr0`/`ts0`; los valores se leen de `src/config.py` (`TR0 = 9 s`, `TS0 = 13 s`),
cumpliendo *"no podrán modificarse, optimizarse ni ajustarse manualmente"*.

---

## 5. Inconsistencias detectadas por las pruebas ampliadas (N-07)

Al extender `test_skfuzzy_equivalence` más allá de su alcance original solo
`automf`, 95 % del rango), la prueba destapó una inconsistencia real:

- **Síntoma:** `compute_crisp` (usado por el fitness) y `controller.compute()` de
  `skfuzzy.control` (usado a medir tiempos y en la evaluación final) **no coincidían**
  en cromosomas optimizados: diferencia de hasta **≈ 0.0037 V**
  (ejemplo: N=5, `e=0.888603, Δe=−0.366565` → skfuzzy `−6.23087` vs exacto `−6.22716`).
- **Causa raíz:** `CrispValueCalculator.defuzz()` de scikit-fuzzy remuestrea el universo
  del consecuente insertando los puntos donde cada función de membresía corta el grado
  de activación (`_interp_universe_fast` → `np.union1d`), y defuzzifica sobre ese
  universo no uniforme. La implementación previa defuzzificaba directamente sobre la
  malla uniforme de 1000 puntos (aproximación trapezoidal distinta).
- **Corrección:** `compute_crisp` replica el procedimiento lineal por línea de
  scikit-fuzzy (cruces → `np.union1d` → `interp_membership` → min/max → `defuzz("centroid")`),
  conservando la semántica Mamdani min–max–centroide.
- **Estado:** el test extendido pasó 5/5 antes de pausar la ejecución; la equivalencia es
  exacta para toda entrada interior del universo (en los vértices exactos del universo
  scikit-fuzzy degenera con μ==0 en todos los términos — `EmptyMembershipError` —
  y `compute_crisp` define la evaluación saturada sobre nodos interiores;
  convención documentada en el docstring de `compute_crisp`).

---

## 6. Matriz de conformidad post-corrección (sobre la nueva versión)

| Requisito del enunciado | Estado en la nueva versión | Evidencia |
|---|---|---|
| Planta `lti([0.5], [1, 13.6667, 23.3487, 0])`, sin modificar | ✔ | `create_plant()` / `config.PLANT_*` |
| Simulación exclusivamente con `scipy.signal.lsim`; sin `odeint`/`solve_ivp`/integradores propios | ✔ (H-01 pendiente de confirmar con el profesor) | `plant_sim.py` + test anti-`expm/odeint/solve_ivp` |
| Referencia cuadrada ±1 rad, período 100 s, ciclo 50 %, sin ruido | ✔ (mejorada, H-03) | `create_time_and_reference()` + test por semiperíodos |
| `T_sim = 200 s`, `x0 = [0,0,0]` | ✔ | `config.T_SIM`, `config.X0` |
| Universos fijos `[−π/2, π/2]`, `[−π/6, π/6]`, `[−8.18, 8.18]` | ✔ | `config.ERROR_*/DERROR_*/VOLTAGE_*` |
| 3 controladores 5/7/9 términos con `automf` evaluados sin GA (Fase 1) | ✔ (código igual que el original, pendiente de regenerar resultados) | `run_single_ga_experiment` → `evaluate_baseline_controller` |
| Fitness Ec. (12) con los 8 objetivos de la Tabla 1 y descarte de [0, 50) s | ✔ (H-05 corregido: promedio de `f`) | `metrics_fitness.py` |
| `tr0 = 9 s`, `ts0 = 13 s` no modificables | ✔ (H-06 corregido) | firma de `evaluate_controller_response` + test |
| Factor de penalización q = Ec. (13) | ✔ (H-04 corregido) | `compute_penalty_factor_q` + tests con `min(h) > −1` |
| Reparación del cromosoma y penalización | ✔ (reparación según original; penalización reportada aparte, H-08) | `chromosome.py` + campos JSON |
| pyGAD exclusivo, mínimo 20 individuos/30 generaciones | ✔ (sin cambio) | `config`/`ga_optimizer.py` |
| Evaluación de CADA individuo: 200 s completos + Ecs. (12) y (13), sin evaluación simplificada (Fase 2) | ✔ (H-08 corregido) | `fitness_func` exacto + `test_ga_uses_exact_inference` |
| Selección del mejor individuo exclusivamente por la función fitness (Fase 3) | ✔ (H-08/N-06 corregidos) | banner de combinación + `best_solution()` |
| 5 corridas con semillas distintas, promedio y desviación estándar (Fase 5) | ✔ (pendiente de regenerar resultados en la raíz) | `main.py` + `plotting_tables.summarize_experiments` |
| Métricas obligatorias: OS[%], SSE[rad], tr/ts[s] | ✔ | `compute_step_metrics` / Tabla obligatoria |
| Tiempo de inferencia con `perf_counter()` sobre `controller.compute()` | ✔ | `measure_inference_time_ms` |
| Tiempo de optimización con `time.time()` alrededor de `ga_instance.run()` | ✔ | `run_single_ga_experiment` |
| Uso de memoria medido | ✔ | `measure_controller_memory_mb` (tracemalloc) |
| Reproducibilidad (`python main.py`) | Pendiente: regenerar la campaña de 15 corridas tras los cambios (H-04/H-08 alteran el fitness de cada individuo) | nueva `results/` en raíz |
| Estructura del reporte (5 secciones) + análisis crítico con evidencia | Pendiente (P1: A-01…A-08, N-01, N-02, N-03) | `build_deliverables.py` a regenerar |

*Leyenda: ✔ = cumplido en código; pendiente = requiere ejecución/regeneración que aún
no se ha corrido por petición del usuario (modo de revisión paso a paso).*

---

## 7. Anomalías reconocidas pero NO corregidas (trabajo pendiente)

De `docs/AUDITORIA_PARCIAL2.md`, fuera del alcance de esta pasada P0:

| ID | Qué queda pendiente |
|---|---|
| H-01 | Confirmar con el profesor si el lazo con `lsim` por intervalo es aceptable; documentar la respuesta. La justificación técnica de diseño ya está en el docstring de `ClosedLoopPlantSimulator`. |
| H-07 | **Resuelto de facto con H-08**: el único muestreo truncado (`voltage_universe[::4]` → ≈ +8.13 V) pertenecía a la tabla 65×65 eliminada. Los tres universos van completos en `np.linspace(-8.18, 8.18, 1000)`; verificado por grep del código actual. |
| H-09 | Diagnóstico implementado: `plant_sim.py` cuenta muestras saturadas de `e`/`Δe` (`n_sat_e`, `e_sat_frac`, `n_sat_de`, `de_sat_frac`) y `ga_optimizer.py` las reporta en el JSON de cada controlador. Queda pendiente discutirlo como **decisión de diseño** en el reporte (con las cifras medidas; ver §10). |
| H-10–H-12 | Genes inertos por picos extremos anclados, traslape mínimo casi nulo y sin penalización, reparación por `sort` sin reescribir el gen: **decisión de diseño documentada** (§10); corregirlos alteraría `get_num_genes` o el espacio de búsqueda ya validado (95/161/243 genes se conservan). |
| **H-13** | **Implementado (P1)**: `MamdaniFuzzyController.measure_rule_coverage(grid_size=129)` mide la fracción de la malla (e, Δe) donde ninguna regla activa se dispara; se reporta en el JSON de cada controlador final (baseline y GA) como `rule_coverage`. Es SOLO diagnóstico: la Ec. (12) no se altera. Test: `test_rule_coverage_and_saturation` (baseline 100 % cubierto; 1 regla → 74.61 % descubierto). Queda pendiente: discutir las cifras de los controladores optimizados en el reporte tras la campaña. |
| H-14 | Sesgo de inicialización hacia más reglas; mutación por reemplazo para genes de activación; término de parsimonia: **decisión de diseño documentada** (§10) — alterarlos cambiaría el protocolo experimental ya definido; el análisis de reglas activas (A-03) se hace con los datos reales en el reporte. |
| H-15 | Configuración en el mínimo exacto (20/30): permitido por el enunciado ("podrán utilizar mayores pero nunca menores"); disponible usar más si el tiempo lo permite. Uso de `--force` al validar cambios (sin caché). |
| A-01…A-08 | Correcciones del análisis crítico y del reporte (×1.07 real vs "10×", prueba estadística Mann-Whitney Q2/Q23, análisis de supresión con datos reales, ablación regla por regla, experimento MOTFF sin q vs RMSE): se corregirán en `build_deliverables.py` **después** de regenerar la campaña, porque cambian todas las cifras. |
| N-01 | Justificación técnica de los pesos (0.125×8): pendiente en `build_deliverables.py` (Metodología del reporte). |
| **N-02** | **Generado (P1)**: justificación técnica completa de `DT = 0.10 s` en la constante `JUSTIFICACION_DT` de `src/config.py` (polos dominantes ≈ −1.92/−11.75 rad/s, 5 muestras por constante de tiempo, resolución relativa de tr/ts ≤ 1.1 %, exactitud de la propagación ZOH independiente de dt, costo 10× si dt = 0.01) y análisis experimental en el módulo `src/dt_sensitivity.py::analyze_dt_sensitivity` (re-simula el mejor controlador con dt = 0.10/0.05/0.02/0.01 s). Pendiente: ejecutarlo sobre los 3 mejores controladores tras la campaña y volcarlo en la Discusión del reporte. |
| N-03 | Alinear la estructura del reporte a las 5 secciones exigidas: pendiente en `build_deliverables.py`. |

---

## 8. Verificación (qué pruéban las pruebas unitarias)

Suite: `uv run python -m tests.test_verification` — **7 pruebas, última ejecución 7/7
superadas** (detalle de ejecución por fase en §10).

1. **`test_plant_and_reference`** — planta exacta; prohibición de `expm/odeint/solve_ivp`;
   signos por semiperíodo con `r[-1] == −1`; consistencia lazo vs `lsim` global
   (`lsim_consistency_error < 1e-9`) con ley de control de prueba (PD).
2. **`test_lsim_loop_final_consistency`** (P1, H-02) — la trayectoria del `lsim` global es
   idéntica a la del lazo paso a paso con 4 leyes: cero, PD, **bang-bang ±8.18 V** y
   constante; medido: `max |diff| = 0.000e+00` en las 4 leyes.
3. **`test_equations_12_and_13`** — q literal: `1.5` en `[-0.5, 0.5]`, `2.0` en
   `[0.2, 0.6]`, piso `1.0` con sobreimpulso, `4.0` en `[-1, -0.5]`, `q ≥ 1e5` plano;
   OS en %; respuesta ideal con `tr=9/ts=13` y fitness > 0.96; firma de
   `evaluate_controller_response` sin `tr0/ts0`.
4. **`test_chromosome_encoding_and_repair`** — tamaños 95/161/243 genes; orden estricto
   `a < b < c`; traslape entre vecinos; reparación de cromosomas extremos.
5. **`test_skfuzzy_equivalence`** — equivalencia `compute_crisp` ⇔ `controller.compute()`
   con `automf` + cromosoma base + 3 aleatorios reparados + 1 patológico forzado a
   reparación; malla completa de fracciones `0 → 1` en e y Δe; `atol=1e-4`.
6. **`test_ga_uses_exact_inference`** — no existe `build_lookup_control_law`;
   `fitness_func` llama `compute_crisp`; el cuerpo del callback no contiene
   `repair_penalty` (no mezcla penalización); el JSON reporta la penalización aparte.
7. **`test_rule_coverage_and_saturation`** (P1, H-13/H-09) — el baseline `automf` cubre
   `100.00 %` de la malla (e, Δe); un controlador con solo la regla (ZE, ZE) activa deja
   `74.61 %` de la malla sin regla disparada (zona muerta, medido); el diagnóstico de
   saturación reporta `e_sat_frac = 0.970` con ganancia agresiva de error, sin alterar
   la trayectoria (`lsim_consistency_error < 1e-9`).

---

## 9. Conclusiones

1. **Los dos bloqueantes (H-04, H-08) quedan corregidos y protegidos por pruebas**, y su
   violación era literal del enunciado (Ec. 13 no implementada y evaluación
   simplificada en el GA — invalidante según *"El incumplimiento de cualquiera de las
   fases invalidará la comparación experimental"*).
2. **La trayectoria evaluada ahora es exactamente la que genera la ley de control**
   (H-02) y el `q` respeta la fórmula literal (H-04), con la decisión `h`/`h0`
   documentada para que el reporte pueda discutirla.
3. La inferencia propia usada por el fitness ya es **equivalente al nivel de máquina** a
   `skfuzzy.control` (N-07) tras replicar el remuestreo de defuzzificación de
   scikit-fuzzy; la optimización del costo (sin tablas, sin reconstruir `ControlSystem`
   por individuo, vectorización numpy) no toca la semántica.
4. Los resultados antiguos quedan **inválidos** para la nueva versión (cambian el fitness
   de cada individuo): la campaña `python main.py` debe regenerarse en la raíz, y con
   ella las tablas/figuras/libreta/reporte (`build_deliverables.py`).
5. El código original se mantiene **intacto** en `codigo de cristian/` como referencia
   auditable del antes y el después.

---

## 10. Avance verificado por fases (P1) — ejecución y decisiones de diseño

### 10.1 Verificación ejecutada contra el enunciado y la auditoría

Contraste del estado de código con `docs/INSTRUCCIONES_PARCIAL2.md` (texto del
enunciado) y `docs/AUDITORIA_PARCIAL2.md` (hallazgos), fase por fase:

| Fase del plan | Ítems | Verificación |
|---|---|---|
| **P0** (fitness/protocolo) | H-04, H-08, H-05, H-06, H-02, H-03, N-07 | Código corregido y protegido por pruebas 1–7; suite **7/7** ejecutada |
| **P1-a** (lazo/lsim) | H-01, H-02 | ZOH alineado (test 2: `0.000e+00` en 4 leyes); pregunta al profesor lista (`docs/P1_H01_H02_LSIM.md` §2, 3 puntos); scipy 1.18.1 sin deprecación de `interp` |
| **P1-b** (fitness/codificación) | H-05, H-06, H-07, H-13, H-09, N-02 + decisiones H-04 | Ver §10.2/10.3 abajo; suite ampliada a 7 pruebas, **7/7** ejecutadas |
| **Pendiente** | A-01…A-08, N-01, N-03 | Requieren `build_deliverables.py` nuevo (tras regenerar la campaña) |
| **Pendiente** | ∅ | Regenerar campaña `python main.py --force` (los H-04/H-08 cambiaron el fitness de cada individuo) |

### 10.2 Cambios de código de la fase P1-b (generados y verificados)

| Ítem | Qué se generó | Prueba/evidencia |
|---|---|---|
| **H-13** | `MamdaniFuzzyController.measure_rule_coverage(grid_size=129)` en `fuzzy_controller.py` (`_mfs_on_grid` vectorizado, mismo convenio de nodos interiores que `compute_crisp`) + campo `rule_coverage` en los JSON de baseline y mejor individuo de `ga_optimizer.py`. SOLO diagnóstico: la Ec. (12) no se toca. | `test_rule_coverage_and_saturation`: baseline `automf` → `covered_fraction = 1.0000`; controlador con solo (ZE, ZE) → `uncovered_pct = 74.61` |
| **H-09** | Contadores `n_sat_e`/`n_sat_de`/`e_sat_frac`/`de_sat_frac` en `ClosedLoopPlantSimulator` + campos en los JSON. No cambia la trayectoria (el recorte ya existía; ahora se cuantifica). | `e_sat_frac = 0.970` con ganancia agresiva (medido en test); `lsim_consistency_error < 1e-9` |
| **N-02** | Constante `JUSTIFICACION_DT` en `src/config.py` (5 argumentos: polos dominantes ≈ −1.92/−11.75 rad/s ⇒ 5 muestras por constante de tiempo; resolución relativa de tr/ts ≤ 1.1 %; la propagación ZOH de `lsim` es exacta para cualquier dt ⇒ cambiar dt solo altera el muestreo del controlador y la resolución de métricas; costo ≈ 10× con dt = 0.01) + módulo `src/dt_sensitivity.py::analyze_dt_sensitivity` para la verificación experimental (dt = 0.10/0.05/0.02/0.01 s sobre el mejor controlador). | Constante lista para insertar verbatim en Metodología; análisis a ejecutar sobre los 3 mejores controladores tras la campaña |
| **H-07** | Sin código nuevo: verificado por grep que no resta ningún muestreo truncado del universo; el `[::4]` era de la tabla eliminada por H-08. Universos completos `np.linspace(±..., 1000)`. | Test 1 y 5 garantizan universos completos; strings `::4`/`grid_size` ausentes del código |

### 10.3 Decisiones de diseño documentadas (no corregidas por plan del usuario)

Se conservan deliberadamente (corregir alteraría el espacio de búsqueda o el protocolo
ya validado, y/o añadiría términos fuera de la Ec. 12, que el enunciado obliga a
implementar literalmente). El reporte las discutirá con las cifras de la campaña:

1. **H-10 (genes inertes):** los centros extremos anclados (`u_min + du`, `u_max − du`)
   y `w_left[0]`/`w_right[N-1]` quedan como codificación fija: eliminarlos cambiaría
   `get_num_genes` y los conteos 95/161/243 ya validados por las pruebas. Se documenta
   en el reporte como restricción de codificación.
2. **H-11 (traslape mínimo casi nulo):** la reparación ya garantiza `c_k > a_{k+1}`
   estricto (traslape positivo); añadir una penalización por traslape ~0 añadiría un
   término NO presente en la Ec. 12, que el enunciado obliga a implementar literalmente.
   Se mantiene sin penalización y se discute en el reporte.
3. **H-12 (reparación por `sort`):** la redundancia genotipo↔fenotipo es neutral para
   el resultado (los fenotipos válidos son los que se evalúan); una reparación
   lamarckiana exigiría reescribir la población interna de PyGAD (riesgo de romper la
   semántica del elitismo). Se documenta como decisión de diseño.
4. **H-14 (sesgo de inicialización):** cambiar la tasa de activación inicial o la
   mutación de los genes de activación alteraría el protocolo experimental; el análisis
   A-03 del reporte se hará sobre las reglas activas reales de la nueva campaña.
5. **H-15 (20/30 exactos):** permitido ("podrán utilizar mayores pero nunca menores");
   se usa `--force` para evitar la caché de resultados anteriores.

### 10.4 Registro de ejecución

| Momento | Acción | Resultado |
|---|---|---|
| Tras generar P0+P1-a | `uv run python -m tests.test_verification` | **6/6 superadas** (test del lazo: `0.000e+00` en las 4 leyes) |
| Tras generar P1-b | la misma suite (7 pruebas) | **7/7 superadas**, con nuevos diagnósticos: cobertura baseline `1.0000`, zona muerta 1-regla `74.61 %`, `e_sat_frac` `0.970` |

*La campaña de 15 corridas NO ha sido re-ejecutada aún: los JSON actuales en `results/`
corresponden al código archivado (con H-04/H-08 sin corregir) y deben regenerarse con
`python main.py --force` — proceso ya autorizado por el plan, pendiente de arrancar.*

### 10.5 Comandos de ejecución local (entorno uv)

Todo se ejecuta desde la raíz del repositorio. `uv run` garantiza el uso de `.venv/`
(creado por `uv sync`); **no mezclar con el `python` global del sistema** ni usar
`pip install` manual (el lockfile fija las versiones).

```bash
# 0) Preparar el entorno (primera vez / tras cambiar pyproject.toml)
uv sync                      # dependencias base (numpy, scipy, skfuzzy, pygad, matplotlib)
uv sync --group notebook     # opcional: Jupyter para la libreta
uv sync --group cuda         # opcional: PyTorch CUDA (no requerido por el Parcial)

# 1) Suite de verificación (7 pruebas)
uv run python -m tests.test_verification

# 2) Limpieza opcional de residuos del código archivado antes de la campaña
rm -rf results/smoke

# 3) Campaña completa: 3 baselines + 15 corridas PyGAD (paralelo, ≈ 15–25 min)
uv run python main.py --force
#    (sin --force reutiliza de disco los JSON existentes en results/runs/)

# 4) (Después de 3) Sensibilidad a DT sobre los 3 mejores controladores (N-02):
uv run python -c "
from src.dt_sensitivity import analyze_dt_sensitivity
import numpy as np, json
json_run = json.load(open('results/runs/controller_7terms_seed_42.json'))
tabla = analyze_dt_sensitivity(n_terms=7, chromosome=np.array(json_run['best_chromosome']))
print(json.dumps(tabla, indent=2))
"

# 5) (Después de 1 y 3) Regenerar libreta y reporte — requiere el generador corregido
uv run python build_deliverables.py
```

Estimaciones de tiempo (24 núcleos lógicos, 16 GB RAM): suite ≈ 1–2 min (incluye 9
controladores simulados; el 5/7/9-baseline es lo más pesado); campaña ≈ 15–25 min de
pared; sensibilidad a DT ≈ 30× una simulación de 200 s por controlador (dt = 0.01 cuesta
≈ 10× una corrida del protocolo).
