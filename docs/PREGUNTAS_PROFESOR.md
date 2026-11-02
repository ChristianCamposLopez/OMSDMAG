# Preguntas para el profesor — consulta sobre ambigüedades del Parcial 2

> **Nota de alcance.** Este documento contiene las **5 consultas de ambigüedad** que
> conviene hacerle al profesor sobre puntos que el enunciado no define (lazo con `lsim`,
> retención del actuador, referencia, transiciones negativas, penalización de reparación).
> **No** son las 30 preguntas de análisis crítico de la Parte 5: esas están respondidas
> en **`docs/RESPUESTAS_30_PREGUNTAS.md`**.

Documento de consulta generado en base a `docs/INSTRUCCIONES_PARCIAL2.md` (texto oficial
del enunciado) y al código corregido del repositorio. Para cada pregunta se incluyen:

- **Base normativa:** la cláusula exacta del enunciado que lo motiva.
- **Nuestra implementación:** qué hace el código corregido hoy.
- **Respuesta propuesta:** lo que proponemos como solución correcta, redactado en
  lenguaje simple; es la posición que defendemos en el reporte salvo indicación del
  profesor.
- **Si la respuesta cambia:** el ajuste exacto que habría que hacer al código.

> **Resumen ejecutivo de las 5 preguntas:**
>
> | # | Tema | Decisión que pedimos confirmar |
> |---|---|---|
> | 1 | Cierre del lazo | `lsim` llamado por intervalo para cerrar el lazo con el controlador no lineal |
> | 2 | Retención del actuador | Entrada constante (ZOH) entre muestras del controlador digital |
> | 3 | Referencia cuadrada | Nivel nuevo en cada conmutación; en t = 200 s se mantiene −1 |
> | 4 | Transiciones negativas | Promedio de las contribuciones de las DOS transiciones negativas disponibles |
> | 5 | Penalización de reparación | Reportada aparte, sin restarse al fitness de la Ec. (12) |

---

## Pregunta 1 — ¿Cómo cerrar el lazo con un controlador no lineal usando solo `lsim`?

**Base normativa.** El enunciado exige:

> *"lsim deberá emplearse para simular la respuesta temporal del sistema"* (Parte 1)
> *"La respuesta temporal deberá obtenerse exclusivamente mediante: `tout, theta, xout = lsim(G, U=u, T=t, X0=x0)`"* (Parte 4)

y prohíbe *"integradores numéricos desarrollados por el estudiante"* y *"métodos de
discretización manual"* (Parte 1). Al mismo tiempo aclara que *"u es el voltaje generado
por el controlador difuso"* (Parte 4) y que su código base *"NO resuelve el examen"*
(Parte 4): el lazo debe cerrarse con el controlador Mamdani, que es un mapa no lineal.

**El problema (explicado simple).** La llamada única `lsim(G, U=u, T=t, X0=x0)` necesita
tener escrito el voltaje completo `u(t)` *antes* de simular. Pero en lazo cerrado no se
puede: el voltaje de cada instante depende del error, y el error depende de la salida de
la planta, que todavía no existe. Es un problema causal: no hay forma de precomputar `u`.

**Nuestra implementación** (`src/plant_sim.py`, constante `JUSTIFICACION_LAZO_CERRADO`):

1. En cada instante k el controlador difuso calcula `u[k]` con el error actual.
2. La dinámica de la planta entre muestras se avanza **exclusivamente con
   `scipy.signal.lsim`**: `lsim(G, U=[u_k, u_k], T=[0, dt], X0=x(t_k))`. La única
   biblioteca que integra es scipy; nosotros no programamos ningún integrador.
3. Al final se ejecuta la llamada única del enunciado sobre los 200 s completos
   (`lsim(G, U=u, T=t, X0=x0)`) como **verificación**: si todo está bien, esta
   trayectoria coincide exactamente con la del lazo (comprobado:
   `lsim_consistency_error = 0.000e+00`, test 2 de la suite en 4 leyes de control).

**Respuesta propuesta:** el procedimiento es aceptable porque la restricción real del
enunciado es *quién integra* (scipy, nunca el estudiante), no *cuántas veces* se llama
a `lsim`. El propio enunciado admite que el código base no cierra el lazo y obliga a
usar el voltaje "generado por el controlador difuso", lo que solo es posible
evaluándolo instante a instante.

**Si la respuesta cambia:** contamos con que la verificación final con la llamada
exacta del enunciado permanece; solo variaría el detalle per-intervalo, y la
consistencia entre ambas llamadas está protegida por una prueba unitaria.

---

## Pregunta 2 — ¿Qué retención del actuador: ZOH o interpolación lineal?

**Base normativa.** El enunciado no define cómo se comporta el voltaje del controlador
*entre* dos instantes de muestreo (`dt = 0.10`). La llamada de la Parte 4,
`lsim(G, U=u, T=t, X0=x0)`, no pasa el parámetro `interp`; el valor por defecto es
interpolación lineal, pero también acepta retención de orden cero (`interp=False`).

**El problema (explicado simple).** `scipy.signal.lsim` admite dos supuestos sobre la
entrada entre muestras: mantener el último valor (zero-order hold, ZOH, `interp=False`)
o interpolar linealmente (`interp=True`, el defecto). Cualquiera de los dos es válido,
pero el modo cambia ligeramente la trayectoria, y el enunciado exige que todos los
equipos usen *"el mismo simulador"*.

**Nuestra implementación:** usamos **ZOH** (`interp=False`), que es el modelo natural
de un actuador digital: el controlador difuso muestrea a 10 Hz y su salida se **mantiene
constante** durante cada intervalo `[t_k, t_{k+1})`. El modo está alineado en las dos
llamadas (lazo y verificación final), y si scipy no impone ZOH la respuesta generada
sería distinta.

**Respuesta propuesta:** ZOH es el supuesto físico correcto para un controlador
discreto: entre muestras el DAC/actuador mantiene el último valor; la interpolación
lineal supondría que el voltaje "conoce" el valor futuro a mitad del intervalo, lo que
no cumple causalidad. Está alineado en las dos llamadas, así que la comparación entre
equipos es reproducible mientras todos usen el mismo modo.

**Si la respuesta cambia:** si el profesor prefiere interpolación lineal, se cambia
`interp=False → True` **en ambas llamadas a la vez**; la prueba `test_lsim_loop_final_consistency`
fallará hasta que ambas se alineen (es la red de seguridad).

---

## Pregunta 3 — Convención de la referencia en las conmutaciones y en t = 200 s

**Base normativa.** El enunciado pide la referencia cuadrada con
`r = square(2·π·t/100)` (Parte 4): amplitud ±1 rad, período 100 s, ciclo útil 50 %, y
"«cambiará de signo cada 50 segundos»" (Parte 1). Además la nota de la Parte 2 dice:
*"Descarte las mediciones de la transición de 0 a 1 inicial"*.

**El problema (explicado simple).** La onda cuadrada de scipy deja dos pequeños huecos
de definición: ① en el instante exacto de conmutación (¿t = 50 s vale +1 o −1?); ② en
el último instante de la simulación, `t = 200 s`, porque `square(4π)` termina en un
punto de discontinuidad con un valor convencional ambiguo. Ese segundo hueco es el que
obligaba al código original a parchear a mano la última muestra (`r[-1] = -1.0`).

**Nuestra implementación** (`src/plant_sim.py::create_time_and_reference`): la referencia
se **define explícitamente por semiperíodos** de 50 s, sin `square()`:

```text
[0, 50) s → +1 | [50, 100) s → −1 | [100, 150) s → +1 | [150, 200] s → −1
```

es decir: el controlador "ve" el nivel nuevo **justo en cada conmutación** (t = 50, 100,
150 s) y, en `t = 200 s`, la señal **mantiene el −1 del último semiperíodo**.
La transición ignorada [0, 50) es exactamente la de 0 → +1 que pide descartar la Parte 2.

**Respuesta propuesta:** la definición explícita por semiperíodos reproduce la señal
cuadrada del enunciado sin depender de efectos de borde de `square()` y evita un salto
artificial de +2 rad en la última muestra del horizonte. La convención de conmutación
(coincide con `square` en los puntos interiores) es consistente con el cálculo por
diferencias finitas de Δe.

**Si la respuesta cambia:** solo habría que ajustar la función `create_time_and_reference`;
con el test de signos por semiperíodo (test 1) la referencia queda protegida.

---

## Pregunta 4 — ¿Cómo combinar las DOS transiciones negativas disponibles?

**Base normativa.** La Parte 2 exige *"evaluar obligatoriamente las transiciones
positiva y negativa"* y descartar la inicial 0 → +1. Con la referencia cuadrada de
período 100 s sobre 200 s hay disponibles:

- Transición positiva: una sola disponible (−1 → +1 en [100, 150) s); la primera
  (+1 → 0 → +1 en [0, 50) s) **se descarta** por la nota obligatoria.
- Transición negativa: **dos disponibles** (+1 → −1 en [50, 100) s y en [150, 200] s).

**El problema (explicado simple).** El lado positivo da un número fijo de métricas,
pero ¿qué hacer con las dos negativas? El enunciado exige evaluar "las transiciones"
en plural, sin decidir entre la primera o la segunda.

**Nuestra implementación** (`src/metrics_fitness.py::evaluate_controller_response`),
con la decisión documentada: las métricas f5–f8 se calculan **por cada transición negativa**
separadamente, y al fitness entra el **promedio de las contribuciones** (no de las
métricas, para respetar la forma de la Ec. 12, cuyo lado positivo tiene una sola
transición). El promedio de métricas se conserva únicamente como valor de reporte.

**Respuesta propuesta:** promediar las contribuciones de las dos transiciones negativas
es simétrico respecto a la dirección del movimiento del motor (freno y subida) y reduce
la varianza de la evaluación; el semiciclo descartado por el enunciado es exactamente
el [0, 50) s, así que las dos ventanas negativas evaluadas son las dos que quedan
íntegras en el horizonte.

**Si la respuesta cambia:** si el profesor prefiere usar solo [150, 200] s, basta
con cambiar `evaluate_controller_response` para promediar solo la segunda ventana; el
resto del protocolo no se altera.

---

## Pregunta 5 — ¿La penalización de reparación se resta al fitness o se reporta aparte?

**Base normativa.** Las dos cláusulas del enunciado caben leerse de dos formas:

> *"Los estudiantes deberán implementar mecanismos de: reparación del cromosoma,
> penalización directa del fitness."* (Parte 2)

> *"La selección deberá realizarse utilizando exclusivamente la función fitness
> definida anteriormente."* (Parte 3, Fase 3)

**El problema (explicado simple).** La Parte 2 parece pedir **restar** una penalización
del fitness cuando el cromosoma debe repararse; pero si esa penalización se resta,
la función con la que PyGAD selecciona y ordena individuos ya no es "exclusivamente la
función fitness definida" de la Fase 3: sería una función modificada. Esto es un punto
sensible porque el viejo código restaba la penalización dentro del propio fitness.

**Nuestra implementación** (`src/ga_optimizer.py`, bloque "CÓMO SE COMBINAN…" sobre
`fitness_func`): la reparación existe y se cuantifica (`repair_penalty ≥ 0`, campo del
decodificador), pero **no se resta, escala ni mezcla** con el fitness de la Ec. (12).
El valor se reporta **aparte** en el JSON de cada mejor individuo, junto al campo
`penalty_handling`, que documenta textualmente esta decisión. En la práctica la
reparación ya actúa sobre el fenotipo: el cromosoma se corrige antes de
evaluarse, así que el individuo no obtiene ventaja injusta por estar malformado.

**Respuesta propuesta:** reportar aparte es la lectura coherente con ambas cláusulas:
la Fase 3 es explícita en que la selección usa "exclusivamente la función fitness
definida", y la reparación —como mecanismo de cumplimiento de las restricciones de las
funciones de membresía (`a < b < c`, dentro de universo)— ya garantiza que ningún
individuo sea evaluado inválido, sin alterar la Ec. (12).

**Si la respuesta cambia:** si el profesor confirma que la penalización debe restarse,
basta una línea en `fitness_func` (`fitness_eval -= repair_penalty`) documentada en el
banner; además se recomienda entonces listar explícitamente la magnitud de esa
corrección (`repair_penalty` promedio y máximo por corrida) en el reporte para
