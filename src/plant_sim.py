"""Módulo de la planta del servomotor, señal de referencia y simulación estricta con lsim.

Cumple estrictamente las restricciones de las Partes 1 y 4 de `Parcial 2.pdf`:
- Planta definida exclusivamente con `scipy.signal.lti`.
- Respuesta temporal obtenida exclusivamente mediante `scipy.signal.lsim`
  (sin métodos de discretización manual ni integradores externos).
- Horizonte temporal exacto de 200 s, sin ruido ni perturbaciones.
"""

from typing import Callable, Dict, Tuple
import numpy as np
from scipy.signal import lti, lsim

from src.config import (
    DT,
    DERROR_MAX,
    DERROR_MIN,
    ERROR_MAX,
    ERROR_MIN,
    PLANT_DEN,
    PLANT_NUM,
    REF_PERIOD,
    T_SIM,
    VOLTAGE_MAX,
    VOLTAGE_MIN,
    X0,
)

# Constante textual con la justificacion tecnica del cierre del lazo. El generador del
# reporte (`build_deliverables.py`) la importará e insertará tal cual en la sección de
# Metodología, para que el reporte y el código digan exactamente lo mismo (H-01).
JUSTIFICACION_LAZO_CERRADO = """\
JUSTIFICACIÓN DEL CIERRE DEL LAZO PASO A PASO CON scipy.signal.lsim

El controlador difuso Mamdani es un mapa ESTÁTICO NO LINEAL v = f(e, Δe) implementado
con scikit-fuzzy. En lazo cerrado:

    e[k]   = r(t_k) - θ(t_k)
    Δe[k]  = (e[k] - e[k-1]) / dt
    u[k]   = f(e[k], Δe[k])
    θ(t_{k+1}) = evolución de G(s) con entrada u(t) en [t_k, t_{k+1})

La parte de la dinámica la integra exclusivamente scipy: el enunciado exige que la
respuesta temporal se obtenga con `tout, yout, xout = lsim(G, U=u, T=t, X0=x0)` y
prohíbe integradores desarrollados por el estudiante y métodos de discretización manual.

Por causalidad NO es posible conocer completo el vector U de antemano: u[k] depende de
θ[k], y θ[k] es la salida de G(s) precisamente a esa misma u. La llamada única
`lsim(G, U=u, T=t, X0=x0)` exige tener U precomputado; por eso el enunciado aclara que su
código base "NO resuelve el examen", y define que "u corresponde al voltaje generado por
el controlador difuso": u se genera DURANTE la simulación evaluando el sistema difuso en
cada instante de muestreo.

Procedimiento implementado (la única biblioteca que integra es scipy):
1. El controlador difuso genera u[k] en cada instante k (inferencia Mamdani EXACTA,
   equivalente a `controller.compute()` de skfuzzy.control).
2. La evolución continua del estado entre muestreos se obtiene SIEMPRE con
   scipy.signal.lsim: `lsim(G_ss, U=[u_k, u_k], T=[0, dt], X0=x(t_k), interp=False)`.
   La integración interna (exponencial de matriz del sistema aumentado en ZOH) es de
   scipy.signal, no del estudiante, y por tanto no viola las restricciones.
3. El actuador se modela con retención de orden cero (ZOH): el controlador difuso digital
   muestrea en 10 Hz y su salida se mantiene constante en [t_k, t_{k+1}).
4. Al final se ejecuta la llamada única y obligatoria del enunciado sobre el horizonte
   completo, con el MISMO modo de interpolación que el lazo:
   `tout, theta, xout = lsim(G, U=u, T=t, X0=x0, interp=False)`. Con interp=False
   scipy aplica ZOH desde U[i-1], exactamente como el lazo, así que la trayectoria
   verificada coincide con la que generó la ley de control
   (lsim_consistency_error teóricamente 0; el test exige < 1e-9).
5. Métricas y fitness se calculan sobre esa trayectoria verificada del lsim global.

Consecuencia práctica: si el evaluador prefiriera interp=True (interpolación lineal de la
entrada), habría que cambiar AMBAS llamadas a la vez, porque el modo de interpolación es
el modo de operación del lazo; cualquier desalineación produciría una respuesta evaluada
distinta de la simulada (hallazgo H-02 del archivo viejo).
"""


def create_plant() -> lti:
    """Construye la función de transferencia obligatoria del servomotor.

    G(s) = 0.5 / (s^3 + 13.6667 s^2 + 23.3487 s)
    """
    G = lti(PLANT_NUM, PLANT_DEN)
    return G


def create_time_and_reference(
    dt: float = DT, t_sim: float = T_SIM
) -> Tuple[np.ndarray, np.ndarray]:
    """Genera el vector de tiempo [0, 200] s y la referencia cuadrada de ±1 rad.

    La referencia se define de forma explícita por semiperíodos de 50 s sobre el
    intervalo cerrado [0, 200] s:

        [0, 50) s -> +1,  [50, 100) s -> -1,  [100, 150) s -> +1,  [150, 200] s -> -1

    El instante final t = 200 s pertenece al último semiperíodo (valor -1) porque
    ese es el valor que la señal mantiene hasta el final del horizonte de simulación.
    Así se evita un salto artificial de +2 rad en la última muestra.
    """
    t = np.arange(0.0, t_sim + dt / 2.0, dt)
    half_period = REF_PERIOD / 2.0
    last_segment = int(round(t_sim / half_period)) - 1
    segment = np.minimum(
        np.floor(t / half_period + 1e-9).astype(int), last_segment
    )
    r = np.where(segment % 2 == 0, 1.0, -1.0)
    return t, r


class ClosedLoopPlantSimulator:
    """Simulador en lazo cerrado que utiliza estrictamente `scipy.signal.lsim`.

    En cada instante de muestreo k el controlador difuso calcula el voltaje u[k] a
    partir del error e[k] y del cambio del error de[k]. Como el lazo es no lineal,
    el voltaje no puede conocerse de antemano: se mantiene constante (ZOH) durante
    el intervalo [t_k, t_{k+1}) y la evolución del estado continuo se obtiene
    invocando exclusivamente `scipy.signal.lsim` con condición inicial igual al
    estado actual. Al completar el horizonte de 200 s se ejecuta la verificación
    global `lsim(G, U=u, T=t, X0=x0, interp=False)`, usando el mismo modo de
    interpolación (ZOH) que el lazo para que la trayectoria evaluada sea
    exactamente la que generó la ley de control.

    Justificacion tecnica completa (H-01 / H-02): constante de modulo
    `JUSTIFICACION_LAZO_CERRADO` — el reporte del examen la inserta tal cual.
    Compatibilidad de `interp` (H-02): es un parámetro documentado y NO deprecado de
    `scipy.signal.lsim` en scipy 1.18.1; su docstring dice literalmente:
    "Whether to use linear (True, the default) or zero-order-hold (False)
    interpolation for the input array".
    """

    def __init__(self, dt: float = DT, t_sim: float = T_SIM) -> None:
        self.dt = float(dt)
        self.t_sim = float(t_sim)
        self.G = create_plant()
        # Representación LTI de espacio de estados interna de SciPy para invocar lsim
        self.G_ss = self.G.to_ss()
        self.t, self.r = create_time_and_reference(dt=self.dt, t_sim=self.t_sim)
        self.x0 = np.array(X0, dtype=float)
        self.t_step = np.array([0.0, self.dt], dtype=float)

    def simulate(
        self, control_law: Callable[[float, float], float]
    ) -> Dict[str, np.ndarray]:
        """Simula el sistema en lazo cerrado durante los 200 s usando exclusivamente `lsim`.

        Parámetros
        ----------
        control_law : Callable[[float, float], float]
            Función que recibe (error, derror) en el instante actual y devuelve
            el voltaje de control v(t) generado por el controlador difuso Mamdani.

        Retorna
        -------
        dict con llaves: 't', 'r', 'u', 'theta', 'theta_loop', 'xout', 'e', 'de',
        'lsim_consistency_error', 'n_sat_e', 'n_sat_de', 'e_sat_frac',
        'de_sat_frac' (diagnóstico H-09 de saturación de entradas).
        """
        n_steps = len(self.t)
        u = np.zeros(n_steps, dtype=float)
        u_step = np.zeros(2, dtype=float)
        x_curr = self.x0.copy()
        theta_k = 0.0
        prev_e = 0.0
        theta_loop = np.zeros(n_steps, dtype=float)

        # Diagnóstico H-09: cuántas muestras saturan en los bordes del universo.
        # NO modifica la trayectoria: el recorte ya existía; ahora se cuantifica.
        n_sat_e = 0
        n_sat_de = 0

        inv_dt = 1.0 / self.dt
        r_list = self.r.tolist()
        e_min, e_max = float(ERROR_MIN), float(ERROR_MAX)
        de_min, de_max = float(DERROR_MIN), float(DERROR_MAX)
        v_min, v_max = float(VOLTAGE_MIN), float(VOLTAGE_MAX)
        t_step = self.t_step
        g_ss = self.G_ss

        for k in range(n_steps):
            # u[k] debe decidirse ANTES de avanzar el intervalo: el mapa v = f(e, Δe)
            # es no lineal y causal, por eso no es viable una única llamada global
            # con U precomputado (justificación completa en JUSTIFICACION_LAZO_CERRADO).
            e_k = r_list[k] - theta_k
            de_k = 0.0 if k == 0 else (e_k - prev_e) * inv_dt
            prev_e = e_k

            # Acotar entradas al universo de discurso fijo para consulta segura en skfuzzy
            e_clamped = e_min if e_k < e_min else (e_max if e_k > e_max else e_k)
            de_clamped = de_min if de_k < de_min else (de_max if de_k > de_max else de_k)

            # Contadores de saturación (H-09): |e| llega a 2 rad en cada conmutación,
            # pero el universo de error es [-π/2, π/2]; se cuantifica cuántas muestras
            # se acotan (el comportamiento de control NO cambia).
            if e_clamped != e_k:
                n_sat_e += 1
            if de_clamped != de_k:
                n_sat_de += 1

            v_k = float(control_law(e_clamped, de_clamped))
            if v_k < v_min:
                v_k = v_min
            elif v_k > v_max:
                v_k = v_max
            u[k] = v_k
            theta_loop[k] = theta_k

            if k < n_steps - 1:
                u_step[0] = v_k
                u_step[1] = v_k
                # Propagación del estado continuo mediante scipy.signal.lsim exclusivamente
                _, y_step, x_step = lsim(
                    g_ss, U=u_step, T=t_step, X0=x_curr, interp=False
                )
                theta_k = float(y_step[-1])
                x_curr = x_step[-1]

        # Verificación obligatoria sobre el horizonte completo de 200 s con el mismo
        # modo ZOH usado en el lazo (interp=False). En scipy 1.18.1 la implementación
        # ZOH de lsim avanza con `xout[i] = xout[i-1] @ Ad + U[i-1] @ Bd`, es decir,
        # mantiene el valor de U al INICIO de cada intervalo, igual que el lazo: las
        # dos trayectorias deben coincidir (se verifica con lsim_consistency_error).
        tout, theta, xout = lsim(self.G, U=u, T=self.t, X0=self.x0, interp=False)

        # Cálculo obligatorio del error y cambio del error (Parcial 2.pdf, pág. 13)
        e = self.r - theta
        de = np.diff(e, prepend=e[0]) / self.dt

        max_diff = float(np.max(np.abs(theta - theta_loop)))

        return {
            "t": tout,
            "r": self.r,
            "u": u,
            "theta": theta,
            "theta_loop": theta_loop,
            "xout": xout,
            "e": e,
            "de": de,
            "lsim_consistency_error": max_diff,
            "n_sat_e": int(n_sat_e),          # H-09: muestras con e fuera del universo
            "n_sat_de": int(n_sat_de),        # H-09: muestras con Δe fuera del universo
            "e_sat_frac": n_sat_e / float(n_steps),
            "de_sat_frac": n_sat_de / float(n_steps),
        }
