"""Codificación genética, decodificación y reparación de cromosomas para PyGAD.

Cumple con las restricciones de la Parte 2 de `Parcial 2.pdf` (págs. 5-6, 13):
- Optimiza simultáneamente:
  1. Funciones de membresía de entrada (`error`, `derror`): centros, anchuras, solapamientos y forma.
  2. Funciones de membresía de salida (`voltage`): centros, anchuras, solapamientos y forma.
  3. Base de reglas difusas: activación/desactivación de reglas (1/0) y consecuentes.
- Garantiza mediante reparación y acotamiento que todas las funciones de membresía
  permanezcan dentro de sus universos de discurso fijos, sin anchuras negativas,
  sin funciones invertidas ni funciones degeneradas.
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
    - 3 variables (error, derror, voltage) x (n_terms centros + 2*n_terms anchuras/solapamientos) = 9 * n_terms
    - n_terms^2 genes de activación de reglas (en [0, 1], activa si >= 0.5)
    - n_terms^2 genes de consecuentes de reglas (en [0, n_terms - 1])
    Total = 9 * n_terms + 2 * (n_terms ** 2)
    """
    return 9 * n_terms + 2 * (n_terms ** 2)


def get_gene_space(n_terms: int) -> List[Dict[str, float]]:
    """Construye el espacio de búsqueda (`gene_space`) acotado para PyGAD."""
    gene_space: List[Dict[str, float]] = []

    # 1. Variable error: n_terms centros + 2*n_terms factores de anchura/solapamiento
    for _ in range(n_terms):
        gene_space.append({"low": float(ERROR_MIN), "high": float(ERROR_MAX)})
    for _ in range(2 * n_terms):
        gene_space.append({"low": 0.20, "high": 1.80})

    # 2. Variable derror: n_terms centros + 2*n_terms factores de anchura/solapamiento
    for _ in range(n_terms):
        gene_space.append({"low": float(DERROR_MIN), "high": float(DERROR_MAX)})
    for _ in range(2 * n_terms):
        gene_space.append({"low": 0.20, "high": 1.80})

    # 3. Variable voltage: n_terms centros + 2*n_terms factores de anchura/solapamiento
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
    """Genera el cromosoma equivalente al controlador Baseline (`automf` + tabla PD simétrica)."""
    genes: List[float] = []

    for u_min, u_max in [
        (ERROR_MIN, ERROR_MAX),
        (DERROR_MIN, DERROR_MAX),
        (VOLTAGE_MIN, VOLTAGE_MAX),
    ]:
        centers = np.linspace(u_min, u_max, n_terms)
        genes.extend(centers.tolist())
        # En automf, cada triángulo toca exactamente los centros vecinos (factor de solapamiento = 1.0)
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
    """Repara y decodifica los parámetros [a, c, b] de las N funciones triangulares.

    Retorna
    -------
    params : np.ndarray de forma (n_terms, 3) con [a_k, c_k, b_k] válidos.
    penalty : float >= 0.0 que cuantifica las reparaciones aplicadas al cromosoma.
    """
    penalty = 0.0
    span = float(u_max - u_min)
    min_sep = 1e-3 * span / max(n_terms, 1)

    # Penalizar si algún centro estaba fuera de rango o desordenado antes de reparar
    out_of_bounds = np.sum((raw_centers < u_min) | (raw_centers > u_max))
    if out_of_bounds > 0:
        penalty += 0.02 * float(out_of_bounds)

    if np.any(np.diff(raw_centers) <= 0):
        penalty += 0.02

    # 1. Reparación de rango y orden estricto de los centros
    centers = np.clip(raw_centers, u_min, u_max)
    centers = np.sort(centers)

    # Fijar extremos o garantizar separación mínima para evitar funciones degeneradas
    for k in range(1, n_terms):
        if centers[k] - centers[k - 1] < min_sep:
            centers[k] = min(u_max, centers[k - 1] + min_sep)
    for k in range(n_terms - 2, -1, -1):
        if centers[k + 1] - centers[k] < min_sep:
            centers[k] = max(u_min, centers[k + 1] - min_sep)

    # 2. Reparación de factores de anchura/solapamiento en [0.20, 1.80]
    if np.any(raw_widths <= 0):
        penalty += 0.05
    widths = np.clip(raw_widths, 0.20, 1.80)
    w_left = widths[:n_terms]
    w_right = widths[n_terms:]

    params = np.zeros((n_terms, 3), dtype=float)
    for k in range(n_terms):
        c_k = float(centers[k])
        if k == 0:
            a_k = float(u_min)
            c_k = float(u_min)  # Como en automf, el extremo izquierdo tiene pico en u_min
            dist_right = max(float(centers[1] - c_k), min_sep)
            b_k = min(float(u_max), c_k + float(w_right[k]) * dist_right)
        elif k == n_terms - 1:
            b_k = float(u_max)
            c_k = float(u_max)  # Como en automf, el extremo derecho tiene pico en u_max
            dist_left = max(float(c_k - centers[n_terms - 2]), min_sep)
            a_k = max(float(u_min), c_k - float(w_left[k]) * dist_left)
        else:
            dist_left = max(float(c_k - centers[k - 1]), min_sep)
            dist_right = max(float(centers[k + 1] - c_k), min_sep)
            a_k = max(float(u_min), c_k - float(w_left[k]) * dist_left)
            b_k = min(float(u_max), c_k + float(w_right[k]) * dist_right)

        # Garantizar no-degeneración: a_k <= c_k <= b_k y b_k > a_k
        a_k = min(a_k, c_k)
        b_k = max(b_k, c_k)
        if b_k - a_k < min_sep:
            if c_k + min_sep <= u_max:
                b_k = c_k + min_sep
            else:
                a_k = c_k - min_sep

        params[k, 0] = a_k
        params[k, 1] = c_k
        params[k, 2] = b_k

    return params, penalty


def decode_chromosome(chromosome: np.ndarray, n_terms: int) -> Dict[str, object]:
    """Decodifica y repara un cromosoma de PyGAD hacia la estructura del controlador difuso.

    Retorna un diccionario con:
    - 'error_mfs': ndarray (n_terms, 3) con [a, c, b] en [-pi/2, pi/2]
    - 'derror_mfs': ndarray (n_terms, 3) con [a, c, b] en [-pi/6, pi/6]
    - 'voltage_mfs': ndarray (n_terms, 3) con [a, c, b] en [-8.18, 8.18]
    - 'rule_active': ndarray booleano (n_terms, n_terms)
    - 'rule_consequent': ndarray entero (n_terms, n_terms) con valores en 0..n_terms-1
    - 'active_rules_list': lista legible de reglas activas (ej. 'IF error IS ZE AND derror IS ZE THEN voltage IS ZE')
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

