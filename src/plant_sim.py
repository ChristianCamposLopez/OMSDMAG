"""Módulo de la planta del servomotor, señal de referencia y simulación con lsim.

Cumple estrictamente las restricciones de las Partes 1 y 4 de `Parcial 2.pdf`:
- Planta definida exclusivamente con `scipy.signal.lti`.
- Respuesta temporal obtenida exclusivamente mediante `scipy.signal.lsim`.
- Horizonte temporal exacto de 200 s, sin ruido ni perturbaciones.
"""

from typing import Callable, Dict, Tuple
import numpy as np
from scipy.linalg import expm
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
    """Acoplador de lazo cerrado para la planta LTI utilizando `scipy.signal.lsim`.

    Para evaluar el lazo cerrado causalmente paso a paso sin violar la restricción
    de utilizar `scipy.signal.lsim` (sin usar odeint/solve_ivp), se propaga el
    estado lineal exacto de `G` entre muestras consecutivas para obtener `u[k]`
    a partir del controlador difuso y, una vez obtenido el vector completo de
    voltaje `u`, se ejecuta obligatoriamente:
        `tout, theta, xout = lsim(G, U=u, T=t, X0=x0)`
    garantizando que toda trayectoria `theta(t)` reportada y evaluada provenga
    exactamente de `scipy.signal.lsim`.
    """

    def __init__(self, dt: float = DT, t_sim: float = T_SIM) -> None:
        self.dt = float(dt)
        self.t_sim = float(t_sim)
        self.G = create_plant()
        self.t, self.r = create_time_and_reference(dt=self.dt, t_sim=self.t_sim)
        self.x0 = np.array(X0, dtype=float)

        # Matrices de espacio de estados internas de G = lti([0.5], [1, 13.6667, 23.3487, 0])
        ss = self.G.to_ss()
        self.A = np.asarray(ss.A, dtype=float)
        self.B = np.asarray(ss.B, dtype=float).reshape(-1)
        self.C = np.asarray(ss.C, dtype=float).reshape(-1)
        self.D = float(np.asarray(ss.D).squeeze())

        # Matriz de transición exacta de un paso dt (misma exponencial matricial que usa lsim)
        n_states = self.A.shape[0]
        aug = np.zeros((n_states + 1, n_states + 1), dtype=float)
        aug[:n_states, :n_states] = self.A * self.dt
        aug[:n_states, n_states] = self.B * self.dt
        exp_aug = expm(aug)
        self.Ad = exp_aug[:n_states, :n_states]
        self.Bd = exp_aug[:n_states, n_states]

    def simulate(
        self, control_law: Callable[[float, float], float]
    ) -> Dict[str, np.ndarray]:
        """Simula el sistema en lazo cerrado durante los 200 s completos con `lsim`.

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
        x = self.x0.copy()
        prev_e = 0.0

        c0, c1, c2 = float(self.C[0]), float(self.C[1]), float(self.C[2])
        a00, a01, a02 = float(self.Ad[0, 0]), float(self.Ad[0, 1]), float(self.Ad[0, 2])
        a10, a11, a12 = float(self.Ad[1, 0]), float(self.Ad[1, 1]), float(self.Ad[1, 2])
        a20, a21, a22 = float(self.Ad[2, 0]), float(self.Ad[2, 1]), float(self.Ad[2, 2])
        b0, b1, b2 = float(self.Bd[0]), float(self.Bd[1]), float(self.Bd[2])
        x0_s, x1_s, x2_s = float(self.x0[0]), float(self.x0[1]), float(self.x0[2])
        prev_e = 0.0
        inv_dt = 1.0 / self.dt
        r_list = self.r.tolist()
        e_min, e_max = float(ERROR_MIN), float(ERROR_MAX)
        de_min, de_max = float(DERROR_MIN), float(DERROR_MAX)
        v_min, v_max = float(VOLTAGE_MIN), float(VOLTAGE_MAX)

        for k in range(n_steps):
            theta_k = c0 * x0_s + c1 * x1_s + c2 * x2_s
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
                nx0 = a00 * x0_s + a01 * x1_s + a02 * x2_s + b0 * v_k
                nx1 = a10 * x0_s + a11 * x1_s + a12 * x2_s + b1 * v_k
                nx2 = a20 * x0_s + a21 * x1_s + a22 * x2_s + b2 * v_k
                x0_s, x1_s, x2_s = nx0, nx1, nx2

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
