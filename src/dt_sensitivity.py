"""Análisis de sensibilidad del paso temporal DT sobre un controlador dado (N-02).

Responde directamente al hallazgo N-02 de `docs/AUDITORIA_PARCIAL2.md`:
el enunciado ejemplifica dt = 0.01 s pero permite cambiar la resolución si se
justifica tecnicamente. La justificacion del proyecto (por que DT = 0.10 s en el
protocolo) está en la constante `JUSTIFICACION_DT` de `src/config.py`, que el
reporte inserta verbatim; este módulo añade la VERIFICACIÓN EXPERIMENTAL:
re-simula el mismo controlador con pasos más finos y compara fitness y métricas.

IMPORTANTE: es un análisis de diagnóstico para la discusión del reporte.
NO forma parte del protocolo obligatorio (el protocolo usa DT de `src/config.py`
en todas las 15 corridas) y NO altera la Ec. (12). Costo estimado: cada paso más
fino multiplica los pasos del lazo: dt=0.01 cuesta ≈ 10× una simulación muestreo
del protocolo; por convención se ejecuta solo sobre los 3 mejores controladores
(uno por configuración) después de regenerar la campaña.

Uso (tras tener la campaña en results/runs/):

    from src.dt_sensitivity import analyze_dt_sensitivity
    tabla = analyze_dt_sensitivity(n_terms=7, chromosome=np.array(json["best_chromosome"]))
"""

from typing import Dict, List, Optional, Sequence
import numpy as np

from src.config import DT, T_SIM
from src.fuzzy_controller import MamdaniFuzzyController
from src.metrics_fitness import evaluate_controller_response
from src.plant_sim import ClosedLoopPlantSimulator


def analyze_dt_sensitivity(
    n_terms: int,
    chromosome: Optional[np.ndarray] = None,
    use_automf_baseline: bool = False,
    dt_values: Sequence[float] = (0.10, 0.05, 0.02, 0.01),
) -> List[Dict[str, float]]:
    """Re-simula un controlador con distintos pasos temporales y compara métricas.

    Parámetros
    ----------
    n_terms : int
        Número de términos lingüísticos (5, 7 o 9).
    chromosome : np.ndarray opcional
        Cromosoma del controlador a analizar; si es None se usa el baseline
        `automf` (útil para contrastar N=5 sobre un caso fijo).
    use_automf_baseline : bool
        True para analizar un controlador base con `automf`.
    dt_values : secuencia de float
        Pasos temporales a comparar. El primero debería ser DT del protocolo
        (0.10 s) para servir de referencia.

    Retorna
    -------
    lista de dicts con:
        'dt', 'n_steps', 'fitness', 'fitness_delta' (vs. el paso de referencia),
        'OS_pos', 'SSE_pos', 'tr_pos', 'ts_pos', 'q_pos',
        'OS_neg', 'SSE_neg', 'tr_neg', 'ts_neg', 'q_neg',
        'lsim_consistency_error' (siempre debe ser ≈ 0 en todos los pasos).
    """
    results: List[Dict[str, float]] = []
    reference_fitness: Optional[float] = None

    for dt in dt_values:
        ctrl_obj = MamdaniFuzzyController(
            n_terms=n_terms,
            chromosome=chromosome,
            use_automf_baseline=use_automf_baseline,
            build_control_system_graph=False,
        )
        simulator = ClosedLoopPlantSimulator(dt=float(dt), t_sim=T_SIM)
        sim = simulator.simulate(ctrl_obj.compute_crisp)
        res = evaluate_controller_response(sim["t"], sim["theta"])

        fitness = float(res["fitness"])
        if reference_fitness is None:
            reference_fitness = fitness

        results.append(
            {
                "dt": float(dt),
                "n_steps": int(len(sim["t"])),
                "fitness": fitness,
                "fitness_delta": float(fitness - reference_fitness),
                "OS_pos": float(res["OS_pos"]),
                "SSE_pos": float(res["SSE_pos"]),
                "tr_pos": float(res["tr_pos"]),
                "ts_pos": float(res["ts_pos"]),
                "q_pos": float(res["q_pos"]),
                "OS_neg": float(res["OS_neg"]),
                "SSE_neg": float(res["SSE_neg"]),
                "tr_neg": float(res["tr_neg"]),
                "ts_neg": float(res["ts_neg"]),
                "q_neg": float(res["q_neg"]),
                "lsim_consistency_error": float(sim["lsim_consistency_error"]),
                "e_sat_frac": float(sim["e_sat_frac"]),
                "de_sat_frac": float(sim["de_sat_frac"]),
            }
        )

    return results
