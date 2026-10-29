"""Codificación genética, decodificación y reparación de cromosomas para PyGAD.

Cumple con las restricciones de la Parte 2 de `Parcial 2.pdf` (págs. 5-6, 13) y
las indicaciones del profesor:
- Optimiza simultáneamente:
  1. Funciones de membresía triangulares de entrada (`error`, `derror`): centros, anchuras,
     traslapes y forma establecidos por el algoritmo genético, cuidando que siempre
     exista un orden estricto en los parámetros a, b y c (es decir, a < b < c).
  2. Funciones de membresía triangulares de salida (`voltage`): centros, anchuras,
     traslapes y forma con orden estricto a < b < c.
  3. Base de reglas difusas: activación/desactivación de reglas (1/0) y consecuentes.
- Garantiza mediante reparación y penalización que todas las funciones de membresía
  permanezcan dentro de sus universos de discurso fijos, cumpliendo estrictamente
  u_min <= a < b < c <= u_max para todo conjunto difuso.
"""

from typing import Dict, List, Tuple
import numpy as np

from src.config import (
    DERROR_MAX,
    DERROR_MIN,
    ERROR_MAX,
    ERROR_MIN,
    LINGUISTIC_LABELS,
    VOLTAGE_MAX,
    VOLTAGE_MIN,
)


def get_num_genes(n_terms: int) -> int:
    """Calcula el número total de genes optimizables para `n_terms` términos.

    Estructura del cromosoma:
    - 3 variables (error, derror, voltage) x (n_terms centros b_k + 2*n_terms anchuras/traslapes para a_k y c_k) = 9 * n_terms
    - n_terms^2 genes de activación de reglas (en [0, 1], activa si >= 0.5)
    - n_terms^2 genes de consecuentes de reglas (en [0, n_terms - 1])
    Total = 9 * n_terms + 2 * (n_terms ** 2)
    """
    return 9 * n_terms + 2 * (n_terms ** 2)


def get_gene_space(n_terms: int) -> List[Dict[str, float]]:
    """Construye el espacio de búsqueda (`gene_space`) acotado para PyGAD."""
    gene_space: List[Dict[str, float]] = []

    # 1. Variable error: n_terms centros b_k + 2*n_terms factores de anchura/traslape (a_k, c_k)
    for _ in range(n_terms):
        gene_space.append({"low": float(ERROR_MIN), "high": float(ERROR_MAX)})
    for _ in range(2 * n_terms):
        gene_space.append({"low": 0.20, "high": 1.80})

    # 2. Variable derror: n_terms centros b_k + 2*n_terms factores de anchura/traslape (a_k, c_k)
    for _ in range(n_terms):
        gene_space.append({"low": float(DERROR_MIN), "high": float(DERROR_MAX)})
    for _ in range(2 * n_terms):
        gene_space.append({"low": 0.20, "high": 1.80})

    # 3. Variable voltage: n_terms centros b_k + 2*n_terms factores de anchura/traslape (a_k, c_k)
    for _ in range(n_terms):
        gene_space.append({"low": float(VOLTAGE_MIN), "high": float(VOLTAGE_MAX)})
    for _ in range(2 * n_terms):
        gene_space.append({"low": 0.20, "high": 1.80})

    # 4. Activación de reglas: n_terms^2 genes continuos en [0, 1] (umbral 0.5 -> {0, 1})
    n_rules = n_terms ** 2
    for _ in range(n_rules):
        gene_space.append({"low": 0.0, "high": 1.0})

    # 5. Consecuentes de reglas: n_terms^2 genes en [0, n_terms - 1]
    for _ in range(n_rules):
        gene_space.append({"low": 0.0, "high": float(n_terms - 1)})

    return gene_space


def create_baseline_chromosome(n_terms: int) -> np.ndarray:
    """Genera el cromosoma equivalente al controlador Baseline con orden estricto a < b < c."""
    genes: List[float] = []

    for u_min, u_max in [
        (ERROR_MIN, ERROR_MAX),
        (DERROR_MIN, DERROR_MAX),
        (VOLTAGE_MIN, VOLTAGE_MAX),
    ]:
        span = float(u_max - u_min)
        du = span / 999.0
        centers = np.linspace(u_min, u_max, n_terms)
        centers[0] = float(u_min) + du
        centers[-1] = float(u_max) - du
        genes.extend(centers.tolist())
        # Factores de traslape = 1.0 (cada triángulo toca los centros vecinos)
        genes.extend([1.0] * (2 * n_terms))

    # Todas las reglas activas inicialmente (1.0 >= 0.5)
    n_rules = n_terms ** 2
    genes.extend([1.0] * n_rules)

    # Consecuentes iniciales: tabla Mamdani PD estándar
    mid = (n_terms - 1) // 2
    for i in range(n_terms):
        for j in range(n_terms):
            cons_idx = int(np.clip(i + j - mid, 0, n_terms - 1))
            genes.append(float(cons_idx))

    return np.array(genes, dtype=float)


def _decode_variable_mfs(
    raw_centers: np.ndarray,
    raw_widths: np.ndarray,
    u_min: float,
    u_max: float,
    n_terms: int,
) -> Tuple[np.ndarray, float]:
    """Repara y decodifica los parámetros [a, b, c] de las N funciones triangulares.

    Garantiza que:
    1. Todas las funciones estén dentro del universo [u_min, u_max].
    2. Siempre exista el orden estricto a_k < b_k < c_k para todo k = 0..n_terms-1.
    3. Los centros cumplan b_0 < b_1 < ... < b_{n_terms-1}.
    4. Se formen traslapes válidos entre conjuntos adyacentes (c_k > a_{k+1}).

    Retorna
    -------
    params : np.ndarray de forma (n_terms, 3) con [a_k, b_k, c_k] válidos (a_k < b_k < c_k).
    penalty : float >= 0.0 que cuantifica las reparaciones aplicadas al cromosoma.
    """
    penalty = 0.0
    span = float(u_max - u_min)
    du = span / 999.0
    min_sep = max(du, 1e-3 * span / max(n_terms, 1))

    # Penalizar si algún centro estaba fuera de rango o desordenado antes de reparar
    out_of_bounds = np.sum((raw_centers < u_min) | (raw_centers > u_max))
    if out_of_bounds > 0:
        penalty += 0.02 * float(out_of_bounds)

    if np.any(np.diff(raw_centers) <= 0):
        penalty += 0.02

    # 1. Reparación de rango y orden estricto de los centros b_k dentro de (u_min, u_max)
    centers = np.clip(raw_centers, u_min + du, u_max - du)
    centers = np.sort(centers)
    # Anclar los picos extremos a un paso de malla de los bordes para cubrir todo el universo con a_k < b_k < c_k
    centers[0] = float(u_min) + du
    centers[-1] = float(u_max) - du

    # Garantizar separación mínima entre centros consecutivos
    for k in range(1, n_terms - 1):
        if centers[k] - centers[k - 1] < min_sep:
            centers[k] = min(
                float(u_max) - (n_terms - k) * min_sep, centers[k - 1] + min_sep
            )
    for k in range(n_terms - 2, 0, -1):
        if centers[k + 1] - centers[k] < min_sep:
            centers[k] = max(
                float(u_min) + (k + 1) * min_sep, centers[k + 1] - min_sep
            )

    # 2. Reparación de factores de anchura/traslape en [0.20, 1.80]
    if np.any(raw_widths <= 0):
        penalty += 0.05
    widths = np.clip(raw_widths, 0.20, 1.80)
    w_left = widths[:n_terms]
    w_right = widths[n_terms:]

    params = np.zeros((n_terms, 3), dtype=float)
    for k in range(n_terms):
        b_k = float(centers[k])
        if k == 0:
            a_k = float(u_min)
            b_k = float(u_min) + du  # a_0 < b_0 < c_0 estricto y mu(u[1]) = 1.0
            dist_right = max(float(centers[1] - b_k), min_sep)
            c_k = min(float(u_max), b_k + float(w_right[k]) * dist_right)
        elif k == n_terms - 1:
            c_k = float(u_max)
            b_k = float(u_max) - du  # a_{N-1} < b_{N-1} < c_{N-1} estricto y mu(u[-2]) = 1.0
            dist_left = max(float(b_k - centers[n_terms - 2]), min_sep)
            a_k = max(float(u_min), b_k - float(w_left[k]) * dist_left)
        else:
            dist_left = max(float(b_k - centers[k - 1]), min_sep)
            dist_right = max(float(centers[k + 1] - b_k), min_sep)
            a_k = max(float(u_min), b_k - float(w_left[k]) * dist_left)
            c_k = min(float(u_max), b_k + float(w_right[k]) * dist_right)

        # Garantizar desigualdad estricta: a_k < b_k < c_k
        a_k = min(a_k, b_k - 0.5 * du)
        c_k = max(c_k, b_k + 0.5 * du)
        a_k = max(float(u_min), a_k)
        c_k = min(float(u_max), c_k)

        params[k, 0] = a_k
        params[k, 1] = b_k
        params[k, 2] = c_k

    # Garantizar traslape entre conjuntos vecinos (c_k > a_{k+1}) manteniendo a_k < b_k < c_k
    for k in range(n_terms - 1):
        if params[k, 2] <= params[k + 1, 0]:
            mid_pt = 0.5 * (params[k, 1] + params[k + 1, 1])
            params[k, 2] = min(float(u_max), max(params[k, 2], mid_pt + 0.25 * min_sep))
            params[k + 1, 0] = max(
                float(u_min), min(params[k + 1, 0], mid_pt - 0.25 * min_sep)
            )

    return params, penalty


def decode_chromosome(chromosome: np.ndarray, n_terms: int) -> Dict[str, object]:
    """Decodifica y repara un cromosoma de PyGAD hacia la estructura del controlador difuso.

    Retorna un diccionario con:
    - 'error_mfs': ndarray (n_terms, 3) con [a, b, c] (a < b < c) en [-pi/2, pi/2]
    - 'derror_mfs': ndarray (n_terms, 3) con [a, b, c] (a < b < c) en [-pi/6, pi/6]
    - 'voltage_mfs': ndarray (n_terms, 3) con [a, b, c] (a < b < c) en [-8.18, 8.18]
    - 'rule_active': ndarray booleano (n_terms, n_terms)
    - 'rule_consequent': ndarray entero (n_terms, n_terms) con valores en 0..n_terms-1
    - 'active_rules_list': lista legible de reglas activas
    - 'num_active_rules': int
    - 'repair_penalty': float
    """
    chrom = np.asarray(chromosome, dtype=float).ravel()
    expected_len = get_num_genes(n_terms)
    if len(chrom) != expected_len:
        raise ValueError(
            f"Longitud de cromosoma inválida: {len(chrom)} (se esperaban {expected_len})."
        )

    block = 3 * n_terms
    e_block = chrom[0:block]
    de_block = chrom[block : 2 * block]
    v_block = chrom[2 * block : 3 * block]

    e_mfs, pen_e = _decode_variable_mfs(
        e_block[:n_terms], e_block[n_terms:], ERROR_MIN, ERROR_MAX, n_terms
    )
    de_mfs, pen_de = _decode_variable_mfs(
        de_block[:n_terms], de_block[n_terms:], DERROR_MIN, DERROR_MAX, n_terms
    )
    v_mfs, pen_v = _decode_variable_mfs(
        v_block[:n_terms], v_block[n_terms:], VOLTAGE_MIN, VOLTAGE_MAX, n_terms
    )

    n_rules = n_terms ** 2
    act_start = 3 * block
    cons_start = act_start + n_rules

    raw_active = chrom[act_start:cons_start]
    raw_cons = chrom[cons_start : cons_start + n_rules]

    active_flags = (raw_active >= 0.5).reshape((n_terms, n_terms)).copy()
    cons_indices = np.clip(np.round(raw_cons), 0, n_terms - 1).astype(int).reshape(
        (n_terms, n_terms)
    )

    repair_penalty = pen_e + pen_de + pen_v

    # Reparación si todas las reglas quedaron desactivadas: activar la regla central ZE-ZE
    if not np.any(active_flags):
        mid = n_terms // 2
        active_flags[mid, mid] = True
        cons_indices[mid, mid] = mid
        repair_penalty += 0.25

    labels = LINGUISTIC_LABELS[n_terms]
    active_rules_list: List[str] = []
    rule_idx = 1
    for i in range(n_terms):
        for j in range(n_terms):
            if active_flags[i, j]:
                k = int(cons_indices[i, j])
                active_rules_list.append(
                    f"R{rule_idx:02d} (celda [{i+1},{j+1}]): IF error IS {labels[i]} AND derror IS {labels[j]} THEN voltage IS {labels[k]}"
                )
            rule_idx += 1

    return {
        "n_terms": n_terms,
        "labels": labels,
        "error_mfs": e_mfs,
        "derror_mfs": de_mfs,
        "voltage_mfs": v_mfs,
        "rule_active": active_flags,
        "rule_consequent": cons_indices,
        "active_rules_list": active_rules_list,
        "num_active_rules": int(np.sum(active_flags)),
        "total_possible_rules": n_rules,
        "repair_penalty": float(repair_penalty),
    }
