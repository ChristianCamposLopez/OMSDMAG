"""Cálculo de las 8 métricas transitorias, factor de penalización q (Ec. 13)
y función de aptitud multiobjetivo MOTFF (Ec. 12).

Referencias:
- `Parcial 2.pdf`, páginas 6-8 (Ecuaciones 12 y 13, Tabla 1).
- Téllez-Velázquez et al. (2017), Sección 5.1, Figura 5, Ecuaciones (12)-(13) y Tabla 10 (págs. 9-10, 17).
  * OS se expresa en porcentaje (%) conforme a la Tabla 10 del artículo.
  * SSE se expresa en radianes (rad).
  * tr y ts se expresan en segundos (s).
  * q (rho) se calcula mediante la Ecuación (13) cuando [min(h), max(h)] <= [min(h0), max(h0)],
    siendo q >= 1.0 un factor de penalización que incrementa el denominador q * tr.
"""

from typing import Dict, Sequence
import numpy as np

from src.config import (
    FITNESS_WEIGHTS,
    FIRST_NEG_TRANSITION_WINDOW,
    NEG_TRANSITION_WINDOW,
    POS_TRANSITION_WINDOW,
    TR0,
    TS0,
)


def compute_penalty_factor_q(
    h: np.ndarray, h0_min: float = -1.0, h0_max: float = 1.0
) -> float:
    """Calcula el factor de penalización obligatorio q (rho en Ecuación 13, pág. 10 del artículo).

    Definición del artículo (pág. 10, col. 2, párrafo 1):
        "Here, Greek letter rho is the rise time penalty factor when
         [min(theta):max(theta)] <= [min(theta_0); max(theta_0)], where theta is a
         collection of all the rotor position feedback and theta_0 is a collection
         of all the noise-free reference position signals, both during simulation time.
         This factor prevents rating with a good score all the very short and incorrect
         rise times, when the steady state is reached under the reference value."

        q = (max(h^0) - min(h_i)) / (max(h) - min(h))    (Ec. 13)
    """
    h_max = float(np.max(h))
    h_min = float(np.min(h))
    denom = h_max - h_min

    if denom <= 1e-6:
        return 1e6  # Penalización severa si la respuesta es prácticamente plana

    # Ecuación (13) literal y cobertura pico a pico de la referencia [min(h0), max(h0)]
    q_eq13 = (float(h0_max) - h_min) / denom
    q_span = (float(h0_max) - float(h0_min)) / denom

    return float(max(abs(q_eq13), q_span, 1.0))


def compute_step_metrics(
    t: np.ndarray,
    theta: np.ndarray,
    t_start: float,
    t_end: float,
    r_init: float,
    r_final: float,
    settling_tol: float = 0.05,
) -> Dict[str, float]:
    """Calcula las 4 métricas transitorias (OS [%], SSE [rad], tr [s], ts [s]) y el factor q.

    Parámetros
    ----------
    t : np.ndarray
        Vector temporal completo [s].
    theta : np.ndarray
        Respuesta angular del rotor [rad].
    t_start, t_end : float
        Límites temporales de la ventana de transición (ej. [100, 150) s o [150, 200] s).
    r_init, r_final : float
        Valor inicial y valor objetivo del escalón (-1 -> +1 ó +1 -> -1).
    settling_tol : float
        Banda de tolerancia para el tiempo de establecimiento (5% = 0.05 rad, Artículo pág. 10).
    """
    if t_end < 200.0 - 1e-6:
        mask = (t >= t_start - 1e-9) & (t < t_end - 1e-9)
    else:
        mask = (t >= t_start - 1e-9) & (t <= t_end + 1e-9)
    t_win = t[mask] - t_start
    y_win = theta[mask]
    window_duration = float(t_end - t_start)

    delta_r = float(r_final - r_init)  # +2.0 en transición positiva, -2.0 en negativa
    step_dir = 1.0 if delta_r > 0 else -1.0

    # Respuesta normalizada direccional respecto a la referencia: 0.0 en r_init, 1.0 en r_final
    y_norm = (y_win - r_init) / delta_r

    # 1. Factor de penalización q (Ecuación 13, pág. 10 del artículo)
    q = compute_penalty_factor_q(
        y_win, h0_min=min(r_init, r_final), h0_max=max(r_init, r_final)
    )

    # 2. Tiempo de crecimiento tr [s] (10% a 90%; Figura 5 y pág. 10 del artículo)
    # Verificar que la señal realmente parta por debajo del 10% y cruce del 10% al 90%
    idx_below_10 = np.where(y_norm <= 0.15)[0]
    idx_10 = np.where(y_norm >= 0.10)[0]
    idx_90 = np.where(y_norm >= 0.90)[0]

    if len(idx_below_10) > 0 and len(idx_10) > 0 and len(idx_90) > 0:
        start_search = idx_below_10[0]
        idx_10_valid = idx_10[idx_10 >= start_search]
        if len(idx_10_valid) > 0:
            t_10 = float(t_win[idx_10_valid[0]])
            idx_90_after = idx_90[idx_90 >= idx_10_valid[0]]
            if len(idx_90_after) > 0:
                t_90 = float(t_win[idx_90_after[0]])
                tr = max(t_90 - t_10, float(t[1] - t[0]))
                tr_reached = True
            else:
                tr = window_duration
                tr_reached = False
        else:
            tr = window_duration
            tr_reached = False
    else:
        tr = window_duration
        tr_reached = False

    # 3. Tiempo de establecimiento ts [s] (banda del 5%: |r_final - theta(t)| <= 0.05 rad)
    abs_err = np.abs(r_final - y_win)
    outside_band = np.where(abs_err > settling_tol)[0]

    if not tr_reached:
        ts = window_duration
        settled = False
        ss_start_idx = max(0, int(0.85 * len(y_win)))
    elif len(outside_band) == 0:
        ts = float(t[1] - t[0])
        settled = True
        ss_start_idx = 0
    elif outside_band[-1] < len(y_win) - 1:
        ss_start_idx = int(outside_band[-1] + 1)
        ts = float(t_win[ss_start_idx])
        settled = True
    else:
        # No se estabilizó dentro de la banda del 5% en los 50 s del semiperíodo
        ts = window_duration
        settled = False
        ss_start_idx = max(0, int(0.85 * len(y_win)))

    # 4. Error en estado estable SSE [rad] (promedio del error después de ts; Tabla 10 pág. 17)
    sse = float(np.mean(abs_err[ss_start_idx:]))

    # 5. Sobreimpulso OS en porcentaje [%] (Tabla 10 del artículo, pág. 17)
    directional_excess = step_dir * (y_win - r_final)
    max_excess = float(np.max(directional_excess))
    os_pct = 100.0 * max(0.0, max_excess / abs(r_final))

    return {
        "OS": float(os_pct),
        "SSE": float(sse),
        "tr": float(tr),
        "ts": float(ts),
        "q": float(q),
        "tr_reached": float(tr_reached),
        "settled": float(settled),
    }


def evaluate_controller_response(
    t: np.ndarray,
    theta: np.ndarray,
    weights: Sequence[float] = FITNESS_WEIGHTS,
    tr0: float = TR0,
    ts0: float = TS0,
) -> Dict[str, float]:
    """Evalúa las 8 métricas obligatorias de la Tabla 1 y calcula el fitness total (Ec. 12).

    NOTA OBLIGATORIA (`Parcial 2.pdf` pág. 7):
    Se descartan las mediciones de la transición inicial de 0 a 1 (t in [0, 50) s).
    - Transición Positiva (-1 -> +1): evaluada en [100, 150) s.
    - Transición Negativa (+1 -> -1): evaluada en [150, 200] s (y [50, 100) s).
    """
    w = np.asarray(weights, dtype=float)
    if len(w) != 8 or not np.isclose(np.sum(w), 1.0, atol=1e-6):
        raise ValueError("Los 8 pesos de la función fitness deben sumar exactamente 1.0.")

    # Evaluación de la Transición Positiva (-1 -> +1) en [100, 150) s
    pos = compute_step_metrics(
        t,
        theta,
        t_start=POS_TRANSITION_WINDOW[0],
        t_end=POS_TRANSITION_WINDOW[1],
        r_init=-1.0,
        r_final=1.0,
    )

    # Evaluación de la Transición Negativa (+1 -> -1) en [150, 200] s y [50, 100) s
    neg_second = compute_step_metrics(
        t,
        theta,
        t_start=NEG_TRANSITION_WINDOW[0],
        t_end=NEG_TRANSITION_WINDOW[1],
        r_init=1.0,
        r_final=-1.0,
    )
    neg_first = compute_step_metrics(
        t,
        theta,
        t_start=FIRST_NEG_TRANSITION_WINDOW[0],
        t_end=FIRST_NEG_TRANSITION_WINDOW[1],
        r_init=1.0,
        r_final=-1.0,
    )

    # Promedio de las transiciones negativas posteriores al descarte de [0, 50) s
    neg = {
        "OS": 0.5 * (neg_first["OS"] + neg_second["OS"]),
        "SSE": 0.5 * (neg_first["SSE"] + neg_second["SSE"]),
        "tr": 0.5 * (neg_first["tr"] + neg_second["tr"]),
        "ts": 0.5 * (neg_first["ts"] + neg_second["ts"]),
        "q": 0.5 * (neg_first["q"] + neg_second["q"]),
    }

    # Contribuciones individuales f1..f8 in [0, 1] según Ecuación (12) (Artículo pág. 10)
    f1 = 1.0 / (1.0 + abs(pos["OS"]))
    f2 = 1.0 / (1.0 + abs(pos["SSE"]))
    f3 = min(1.0, float(tr0) / max(pos["q"] * pos["tr"], 1e-6))
    f4 = min(1.0, float(ts0) / max(pos["ts"], 1e-6))

    f5 = 1.0 / (1.0 + abs(neg["OS"]))
    f6 = 1.0 / (1.0 + abs(neg["SSE"]))
    f7 = min(1.0, float(tr0) / max(neg["q"] * neg["tr"], 1e-6))
    f8 = min(1.0, float(ts0) / max(neg["ts"], 1e-6))

    contributions = np.array([f1, f2, f3, f4, f5, f6, f7, f8], dtype=float)
    fitness = float(np.dot(w, contributions))

    # Valor algebraico sin acotar a 1.0 para trazabilidad
    raw_f3 = float(tr0) / max(pos["q"] * pos["tr"], 1e-6)
    raw_f4 = float(ts0) / max(pos["ts"], 1e-6)
    raw_f7 = float(tr0) / max(neg["q"] * neg["tr"], 1e-6)
    raw_f8 = float(ts0) / max(neg["ts"], 1e-6)
    fitness_unclipped = float(
        np.dot(w, np.array([f1, f2, raw_f3, raw_f4, f5, f6, raw_f7, raw_f8]))
    )

    return {
        "fitness": fitness,
        "fitness_unclipped": fitness_unclipped,
        "OS_pos": pos["OS"],
        "SSE_pos": pos["SSE"],
        "tr_pos": pos["tr"],
        "ts_pos": pos["ts"],
        "q_pos": pos["q"],
        "OS_neg": neg["OS"],
        "SSE_neg": neg["SSE"],
        "tr_neg": neg["tr"],
        "ts_neg": neg["ts"],
        "q_neg": neg["q"],
        "f1": float(f1),
        "f2": float(f2),
        "f3": float(f3),
        "f4": float(f4),
        "f5": float(f5),
        "f6": float(f6),
        "f7": float(f7),
        "f8": float(f8),
    }
