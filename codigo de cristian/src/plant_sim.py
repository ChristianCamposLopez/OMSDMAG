"""Módulo de la planta del servomotor, señal de referencia y simulación estricta con lsim.

Cumple estrictamente las restricciones de las Partes 1 y 4 de `Parcial 2.pdf`:
- Planta definida exclusivamente con `scipy.signal.lti`.
- Respuesta temporal obtenida exclusivamente mediante `scipy.signal.lsim`
  (sin métodos de discretización manual ni integradores externos).
- Horizonte temporal exacto de 200 s, sin ruido ni perturbaciones.
"""

from typing import Callable, Dict, Tuple
import numpy as np
from scipy.signal import lti, lsim, square

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


def create_plant() -> lti:
    """Construye la función de transferencia obligatoria del servomotor.

    G(s) = 0.5 / (s^3 + 13.6667 s^2 + 23.3487 s)
    """
    G = lti(PLANT_NUM, PLANT_DEN)
    return G


def create_time_and_reference(
    dt: float = DT, t_sim: float = T_SIM
) -> Tuple[np.ndarray, np.ndarray]:
    """Genera el vector de tiempo [0, 200] s y la señal cuadrada de referencia ±1 rad."""
    t = np.arange(0.0, t_sim + dt / 2.0, dt)
    r = square(2.0 * np.pi * t / REF_PERIOD)
    # Asegurar que en t = 200.0 s permanezca en el estado del último semiperíodo (-1.0)
    if len(r) > 1 and t[-1] >= 200.0:
        r[-1] = -1.0
    return t, r


class ClosedLoopPlantSimulator:
    """Simulador en lazo cerrado que utiliza estrictamente `scipy.signal.lsim`.

    En cada instante de muestreo k, el controlador difuso calcula el voltaje u[k]
    a partir del error e[k] y del cambio del error de[k], y la evolución del estado
    continuo hacia el siguiente instante se obtiene invocando exclusivamente
    `scipy.signal.lsim` con condición inicial X0 igual al estado actual del servomotor.
    Al completar el horizonte de 200 s, se ejecuta:
        `tout, theta, xout = lsim(G, U=u, T=t, X0=x0)`
    cumpliendo de forma literal y estricta la especificación del proyecto.
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
        dict con llaves: 't', 'r', 'u', 'theta', 'xout', 'e', 'de'
        """
        n_steps = len(self.t)
        u = np.zeros(n_steps, dtype=float)
        u_step = np.zeros(2, dtype=float)
        x_curr = self.x0.copy()
        theta_k = 0.0
        prev_e = 0.0

        inv_dt = 1.0 / self.dt
        r_list = self.r.tolist()
        e_min, e_max = float(ERROR_MIN), float(ERROR_MAX)
        de_min, de_max = float(DERROR_MIN), float(DERROR_MAX)
        v_min, v_max = float(VOLTAGE_MIN), float(VOLTAGE_MAX)
        t_step = self.t_step
        g_ss = self.G_ss

        for k in range(n_steps):
            e_k = r_list[k] - theta_k
            de_k = 0.0 if k == 0 else (e_k - prev_e) * inv_dt
            prev_e = e_k

            # Acotar entradas al universo de discurso fijo para consulta segura en skfuzzy
            e_clamped = e_min if e_k < e_min else (e_max if e_k > e_max else e_k)
            de_clamped = de_min if de_k < de_min else (de_max if de_k > de_max else de_k)

            v_k = float(control_law(e_clamped, de_clamped))
            if v_k < v_min:
                v_k = v_min
            elif v_k > v_max:
                v_k = v_max
            u[k] = v_k

            if k < n_steps - 1:
                u_step[0] = v_k
                u_step[1] = v_k
                # Propagación del estado continuo mediante scipy.signal.lsim exclusivamente
                _, y_step, x_step = lsim(
                    g_ss, U=u_step, T=t_step, X0=x_curr, interp=False
                )
                theta_k = float(y_step[-1])
                x_curr = x_step[-1]

        # Llamada obligatoria a scipy.signal.lsim sobre el horizonte completo de 200 s
        tout, theta, xout = lsim(self.G, U=u, T=self.t, X0=self.x0)

        # Cálculo obligatorio del error y cambio del error (Parcial 2.pdf, pág. 13)
        e = self.r - theta
        de = np.diff(e, prepend=e[0]) / self.dt

        return {
            "t": tout,
            "r": self.r,
            "u": u,
            "theta": theta,
            "xout": xout,
            "e": e,
            "de": de,
        }
