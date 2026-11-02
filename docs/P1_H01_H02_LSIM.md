# Fase 2 (P1) — H-01 / H-02: lazo con `lsim` y consistencia

Estado generado **sin ejecutar nada** (modo de revisión paso a paso).

| Ítem pedido | Estado |
|---|---|
| Alineación del modo de interpolación lazo ↔ `lsim` final (H-02) | Hecho: ambas llamadas usan `interp=False` (ZOH). El lsim per-intervalo del lazo ya lo pasaba y la llamada global del código viejo no; ahora quedan alineadas. |
| Test que compare ambas trayectorias | Hecho: `test_lsim_loop_final_consistency` (4 leyes de control; exige igualdad exacta `1e-9`). El test general `test_plant_and_reference` además exige `lsim_consistency_error < 1e-9`. |
| Justificación explícita en el código | Hecho: constante de módulo `JUSTIFICACION_LAZO_CERRADO` en `src/plant_sim.py` (el reporte la importará tal cual) + docstring de `ClosedLoopPlantSimulator` + comentario en el bucle. |
| Justificación en el reporte | Texto disponible: `build_deliverables.py` insertará la constante literal en Metodología cuando se genere (falta generar ese archivo). |
| Pregunta exacta para el profesor | Redactada abajo, lista para copiar. |
| Compatibilidad del parámetro `interp` con la SciPy instalada | Verificada por lectura del fuente de scipy 1.18.1 (abajo). |

---

## 1. ¿POR QUÉ EL LAZO EXIGE EVALUAR u[k] EN CADA INSTANTE? (texto para el reporte)

Resumen del argumento (texto completo en `src/plant_sim.py::JUSTIFICACION_LAZO_CERRADO`):

1. El controlador difuso Mamdani es un **mapa estático no lineal** `v = f(e, Δe)`.
2. `u[k]` depende de `e[k] = r(t_k) − θ(t_k)`, y `θ(t_k)` es la salida de la planta
   `G(s)` precisamente a esa misma `u`. **Por causalidad no puede precomputarse todo
   el vector `U` de antemano**: la llamada única `lsim(G, U=u, T=t, X0=x0)` del código
   base exige tener `U` completo, y el enunciado aclara que ese código base
   *"NO resuelve el examen"*.
3. El propio enunciado define que *"u corresponde al voltaje generado por el controlador
   difuso"*: `u` se genera **durante** la simulación, evaluando el sistema difuso en
   cada instante.
4. La evolución continua entre muestreos se obtiene **exclusivamente con
   `scipy.signal.lsim`** por intervalo (`interp=False`, ZOH) con `X0` igual al estado
   actual. La integración interna (exponencial de matriz del sistema aumentado) es de
   scipy, **no del estudiante**: no viola la prohibición de *"integradores numéricos
   desarrollados por el estudiante"* ni de *"métodos de discretización manual"*.
5. Al final se ejecuta **la llamada única y obligatoria** del horizonte completo con el
   **mismo modo de interpolación** (`interp=False`). Con ZOH, scipy avanza
   `xout[i] = xout[i-1] @ Ad + U[i-1] @ Bd` (mantiene la entrada al inicio del
   intervalo), idéntico al lazo, de modo que la trayectoria evaluada coincide con la
   generada (`lsim_consistency_error = 0.00e+00` en la última medición antes de pausar
   la ejecución; el test exige `< 1e-9`).
6. Métricas y fitness se calculan sobre la trayectoria verificada del `lsim` global,
   no sobre la del lazo.

---

## 2. PREGUNTA EXACTA QUE HAY QUE HACERLE AL PROFESOR

> **Nota:** la versión consolidada de las consultas al profesor — ampliada a 5 preguntas,
> con base normativa, implementación y **respuesta propuesta** para cada una — está en
> **`docs/PREGUNTAS_PROFESOR.md`**. El texto de abajo corresponde al punto 1 (lazo/lsim)
> y se conserva con la versión original del redactado del correo.*

> **Asunto:** Consulta Parcial 2 — cierre del lazo de control con `lsim` y controlador no lineal
>
> Profesor:
>
> El enunciado (Parte 1) pide obtener la respuesta temporal "exclusivamente mediante
> `tout, yout, xout = lsim(G, U=u, T=t, X0=x0)`" y prohíbe integradores desarrollados
> por nosotros y métodos de discretización manual. Sin embargo, con el controlador
> difuso Mamdani el voltaje `u[k]` depende del error `e[k] = r(t_k) − θ(t_k)`, y ` θ(t_k)`
> es la salida de la planta precisamente a esa `u`: por causalidad **no es posible conocer
> el vector `U` completo antes de simular**, y una sola llamada a `lsim` no puede cerrar
> el lazo.
>
> ¿Es aceptable el siguiente procedimiento, y si no lo es, cuál sería el cierre correcto?
>
> 1. El controlador difuso genera `u[k]` en cada instante de muestreo (inferencia Mamdani
>    de `skfuzzy.control`).
> 2. Entre muestreos, la dinámica continua de `G(s)` se avanza con `scipy.signal.lsim`
>    por intervalo: `lsim(G, U=[u_k, u_k], T=[0, dt], X0=x(t_k))`, es decir, **la única
>    biblioteca que integra es scipy.signal** (ningún integrador propio ni
>    discretización manual nuestra).
> 3. Al final se ejecuta la llamada completa del enunciado sobre 200 s,
>    `lsim(G, U=u, T=t, X0=x0)`, como verificación, con el mismo modo de interpolación
>    que el lazo (retención de orden cero, `interp=False`), de modo que esa trayectoria
>    evaluada coincide exactamente con la del lazo.
>
> En concreto le pido decidir tres puntos:
>
> 1. ¿Ese cierre del lazo per-intervalo con `lsim` satisface la restricción
>    "simulación exclusivamente mediante scipy.signal.lsim", aceptando que la
>    integración interna la hace scipy y no el estudiante?
> 2. ¿Holding del actuador: el enunciado no lo define. ¿Es correcto asumir que el
>    voltaje del difuso se mantiene constante (ZOH) durante cada intervalo `[t_k, t_{k+1})`,
>    o prefieren la interpolación lineal de `lsim` por defecto (`interp=True`)? Lo
>    implementamos alineado (ambas llamadas iguales), solo necesito saber cuál modo.
> 3. Convenciones de muestreo de la referencia: (a) ¿el controlador debe "ver" el nuevo
>    nivel de `r(t)` justo en los instantes de conmutación t = 50, 100, 150 s (como
>    implementamos, con `[150, 200]` completo en −1)? y (b) en `t = 200 s`, ¿se mantiene
>    el −1 del último semiperíodo o el +1 que produce `scipy.signal.square` a los 4π?
>    Implementamos mantener −1 (evita un salto artificial de +2 rad en la última muestra).

*Nota interna: los tres puntos están implementados de forma consistente (ZOH alineado,
referencia explícita por semiperíodos con `t=200 → −1`); la consulta busca validar la
elección, no cambiarla sin directriz de respuesta del profesor.*

---

## 3. COMPATIBILIDAD DE `interp` CON LA SCIPI INSTALADA

- **Versión instalada:** scipy 1.18.1 (entorno `uv`, Python 3.13.5).
- **Firma oficial verificada en el fuente** `scipy/signal/_ltisys.py` (línea 2066):
  ```python
  def lsim(system, U, T, X0=None, interp=True): ...
  ```
  y su docstring: *"interp : bool, optional — Whether to use linear (True, the default)
  or zero-order-hold (False) interpolation for the input array."*
- **Sin deprecación:** no hay advertencia ni nota de deprecación en `lsim`; `interp` es
  un parámetro de primera clase (la nota del documento viejo de auditoría sobre SciPy
  reciente quedaba refutada por esta versión).
- **Semántica exacta de `interp=False`** (fuente de scipy 1.18.1):
  ```python
  # Algoritmo ZOH de scipy (implementación interna de lsim):
  M = np.vstack([np.hstack([A * dt, B * dt]),
                 np.zeros((n_inputs, n_states + n_inputs))])
  expMT = linalg.expm(M.T)
  Ad = expMT[:n_states, :n_states]
  Bd = expMT[n_states:, :n_states]
  for i in range(1, n_steps):
      xout[i] = xout[i-1] @ Ad + U[i-1] @ Bd
  ```
  Es decir: con `interp=False` scipy mantiene el valor de `U[i-1]` sobre
  `[t_{i-1}, t_i)` — exactamente el mismo orden de decisión/reacción que el lazo
  per-intervalo. Además impone `T` igualmente espaciado (lo es) y no acepta sistemas
  tiempo-discreto.
- **Por tanto:** la combinación lazo (`interp=False` por intervalo con `X0` actual) +
  verificación global (`interp=False`, `X0=x0`) es **determinista y de igualdad exacta**;
  ningún warning en scipy 1.18.1.

---

## 4. TEST NUEVO (`tests/test_verification.py::test_lsim_loop_final_consistency`)

Para cuatro leyes de control distintas (salida cero, PD lineal, **bang-bang saturada
±8.18 V** que comuta agresivamente cada muestreo, y constante 1.5 V):

1. `theta_evaluada == theta_loop` con `atol=1e-9` (la trayectoria del `lsim` global es
   la misma que la del lazo);
2. el campo `lsim_consistency_error` reporta exactamente ese máximo (`atol=1e-15`);
3. sanidad de `e[0] = r[0] − theta[0]` con `atol=1e-12`.

La ley bang-bang es la prueba más dura: cualquier desalineación de interpolación o de
manejo de `X0` produciría diferencias del orden de milésimas, mucho mayores que `1e-9`.

---

## 5. Pendientes de esta fase

- [ ] Respuesta del profesor (punto 2 del correo, modo de interpolación) → si pide
      `interp=True`, cambiar **ambas** llamadas a la vez; el test dedicado fallará
      hasta alinear, que es la red de seguridad pedida.
- [ ] `build_deliverables.py` nuevo: insertar `JUSTIFICACION_LAZO_CERRADO` literal en
      la sección Metodología del reporte/libreta.
- [x] Re-verificación de la suite: **6/6 superadas** (ejecutada tras generar la fase; el
      test dedicado corrobora `max |theta_lsim - theta_loop| = 0.000e+00` con las 4 leyes).
      Posteriormente la fase P1-fitness añadió una séptima prueba (cobertura/saturación).
