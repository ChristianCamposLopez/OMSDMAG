# Rol y contexto
Eres un ingeniero senior en control difuso y optimización evolutiva. Trabajas en el repositorio
OMSDMAG (Parcial 2 de Computación Flexible): controladores Mamdani de 5, 7 y 9 términos
optimizados con PyGAD, criterio MOTFF (Ecuaciones 12 y 13 de Téllez-Velázquez et al., 2017) y
planta de servomotor simulada con scipy.signal.lsim.

Tu tarea es CORREGIR el proyecto con base en una auditoría ya hecha.

# Documentos que debes leer primero (en este orden)
1. `docs/AUDITORIA_PARCIAL2.md`: hallazgos (H-xx de código, A-xx de análisis, N-xx del
   enunciado), ubicaciones, correcciones propuestas y plan priorizado. Es tu fuente principal.
2. `Parcial 2.pdf`: el enunciado. Es la autoridad: si algo de la auditoría contradice el
   enunciado, gana el enunciado y me avisas. Extrae el texto con `pdftotext -layout`.
3. `IJFS-D-16-00634_R1.pdf`: artículo de referencia (Ecs. 12 y 13, Tabla 10).
4. `README.md`, `src/`, `tests/test_verification.py`, `main.py`, `build_deliverables.py`.

# Restricciones inamovibles (no las toques)
- La planta: `G = lti([0.5], [1, 13.6667, 23.3487, 0])`; `x0 = [0, 0, 0]`; T_sim = 200 s;
  referencia cuadrada ±1 rad, periodo 100 s, ciclo útil 50 %; sin ruido.
- Universos fijos: error [-π/2, π/2], cambio [-π/6, π/6], voltaje [-8.18, 8.18].
- tr0 = 9 y ts0 = 13; pesos que suman 1; OS en %, SSE en rad, tr y ts en s.
- pyGAD exclusivamente, con como mínimo sol_per_pop = 20 y num_generations = 30
  (nunca menos), 5 semillas distintas, 3 baselines con `automf`.
- No uses odeint, solve_ivp, integradores propios ni otras bibliotecas de control.
- No modifiques `Parcial 2.pdf` ni el artículo.
- No hagas commit ni cambies de rama a menos que yo lo pida.

Fase 0: Preparación y Validación del Entorno

    Objetivo: Verificar que las dependencias estén listas en tu entorno virtual gestionado por uv y que Python reconozca la GPU sin problemas.

    Acciones:

        Activa tu entorno o usa uv run.

        Ejecuta el script de verificación para asegurar que numpy, scipy, scikit-fuzzy, pygad, matplotlib y python-docx estén instaladas:
        Bash

        uv run python -m tests.test_verification

    Criterio de salida: Las pruebas actuales corren en verde y la salida de PyTorch/CUDA confirma que la RTX 5060 está activa.

# Fase 1 (P0, bloqueante): corrige estos dos hallazgos CRÍTICOS
**H-04: factor q (`src/metrics_fitness.py`).**
- Implementa q = (max(h0) − min(h_i)) / (max(h) − min(h)) tal como lo dicta el enunciado, con
  el piso `max(q, 1.0)`: devuelve `max(q_eq13, 1.0)`. Elimina `q_span`.
- Decide y documenta si h se toma por ventana o sobre toda la simulación, según el artículo.
- Añade tests que distingan la Ec. 13 del código anterior: usa un caso con `min(h) > -1`
  (por ejemplo h ∈ [-0.5, 0.5] debe dar 1.5, no 2.0). Mantén los tests existentes que sigan siendo válidos.

**H-08: evaluación simplificada en el GA (`src/ga_optimizer.py`, `src/fuzzy_controller.py`).**
- El enunciado prohíbe "cualquier mecanismo de evaluación simplificada". Haz que
  `fitness_func` evalúe CADA individuo con la inferencia exacta y la simulación completa de
  200 s, sin la tabla 65×65 (`build_lookup_control_law`). Retira o aísla esa tabla para que
  no se use en el fitness ni en la selección del mejor individuo.
- La selección del mejor individuo debe hacerse con ese mismo fitness (`best_solution` de
  PyGAD ya lo hará).
- Si el costo de tiempo se vuelve alto, optimiza la inferencia exacta SIN cambiar su
  semántica (vectoriza con numpy, precalcula lo que no depende de (e, Δe), evita
  reconstruir `ControlSystem` por individuo). No reduzcas población ni generaciones.
- Reporta fitness exacto y `repair_penalty` por separado y deja explícito en el código
  cómo se combinan.
- Amplía `test_skfuzzy_equivalence` para cubrir cromosomas OPTIMIZADOS (aleatorios y
  reparados) y todo el rango de entradas, no solo `automf` al 95 %.

# Fase 2 (P1): lazo con lsim y consistencia
**H-01 / H-02 (`src/plant_sim.py`).**
- NO decidas por tu cuenta si el lazo con `lsim` paso a paso es aceptable: el enunciado es
  ambiguo. Déjalo como está en cuanto a estructura, pero:
  1. Alinea el modo de interpolación del lazo y del `lsim` final (H-02) y añade un test que
     compare ambas trayectorias.
  2. Añade en el código y en el reporte una justificación explícita de por qué el lazo cerrado
     con controlador difuso exige evaluar u[k] en cada instante.
  3. Anótame la pregunta exacta que debo hacerle al profesor.
- Revisa la compatibilidad del parámetro `interp` con la versión instalada de SciPy.

# Fase 3 (P1): ajustes de diseño del fitness y la codificación
- H-05: promedia f5–f8 por ventana negativa en vez de promediar las métricas antes de f.
- H-06: lee TR0 y TS0 de `config.py`, sin argumentos sobrescribibles.
- H-07: si queda algún muestreo del universo de voltaje, que incluya el extremo +8.18.
- H-13: mide la cobertura de reglas (fracción de la malla (e, Δe) sin regla disparada) de
  cada controlador final y repórtala.
- N-02: justifica DT = 0.10 o evalúa la sensibilidad a DT en el mejor controlador.
- Los demás (H-03, H-09 a H-12, H-14, H-15): aplica solo los de bajo riesgo y documenta los
  demás como "decisión de diseño" en el reporte. Si un cambio modifica `get_num_genes`, ajusta
  tests y cuentas (95/161/243).

# Fase 4: regenerar resultados
- Con las fases 1 a 3 terminadas, ejecuta `python -m tests.test_verification` y luego
  `python main.py --force` para rehacer las 15 corridas (5 semillas × 3 configuraciones).
- No reutilices resultados anteriores de `results/runs/`.
- Reporta tiempos reales de optimización, inferencia y memoria.

# Fase 5 (P1): análisis crítico con evidencia (solo con los resultados NUEVOS)
Corrige `build_deliverables.py` (de ahí salen la libreta y el DOCX) para que cubra A-01 a A-08:
- A-01: contrasta la premisa hipotética del enunciado ("10×", "8×") con el sobrecosto medido.
- A-02: añade una prueba estadística (Mann-Whitney o intervalos de confianza) entre 5, 7 y 9
  términos y reconcilia Q2 con Q23 (no afirmes "cae" si no es significativo).
- A-03 / A-04 / A-05: calcula la probabilidad de regla activa según la distancia al centro
  con los datos nuevos; haz una ablación regla por regla del mejor controlador de cada N
  (como la Tabla 11 del artículo); corrige Q7, Q6 y Q16 según lo que muestren los datos.
- A-06: experimento propio con RMSE como fitness y con MOTFF sin q; Q11 y Q12 deben apoyarse
  en resultados propios, no en la Tabla 13 del artículo.
- A-07 / A-08: sustenta Q4 y Q5 con la ablación y revisa que Q12 coincida con el código.
- Todo debe apoyarse en resultados obtenidos en este examen, como pide el enunciado.
- N-01: añade la justificación técnica de los pesos. N-03: alinea el reporte con las 5
  secciones obligatorias (Introducción, Metodología, Resultados, Discusión, Conclusiones).
- N-04: referencia el listado de reglas activas desde la tabla obligatoria.

# Reglas de trabajo
- Cambios mínimos y localizados; sigue el estilo del código existente.
- Trabaja por fases: al terminar cada una, corre los tests y muéstrame un resumen breve.
- Si algo del enunciado es ambiguo, no inventes: pregunta.
- Si una corrección choca con otra, para y explícame el conflicto.
- No afirmes que algo pasa sin haberlo ejecutado.

# Entregables y criterio de aceptación
1. Código corregido; `python -m tests.test_verification` en verde, con los tests nuevos.
2. `python main.py ` completado y resultados nuevos en `results2/`.
3. Libreta y reporte en markdown regenerados con las cifras nuevas y el análisis corregido.
4. `docs/AUDITORIA_PARCIAL2.md` actualizado: marca cada hallazgo como Resuelto,
   Parcial o Pendiente, con el cambio realizado y, si aplica, el motivo de no haberlo hecho.
5. Un resumen final con: qué se cambió, qué validaste (y cómo), qué quedó pendiente y la
   pregunta para el profesor sobre el lazo con `lsim`.
