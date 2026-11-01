"""Construcción e inferencia de los controladores difusos Mamdani con `scikit-fuzzy`.

Cumple con todas las restricciones de las Partes 1, 2, 3 y 4 de `Parcial 2.pdf`:
- Uso obligatorio de `skfuzzy` y `skfuzzy.control` (`Antecedent`, `Consequent`, `Rule`,
  `ControlSystem`, `ControlSystemSimulation`), y del evaluador `compute_crisp` que
  reproduce al nivel de máquina ese mismo cómputo.
- Fase 1 (Baselines): generación de funciones de membresía con `automf(N)` para N in {5, 7, 9}.
- Fase 2 (Optimizados): construcción con los parámetros decodificados del cromosoma.
- Medición obligatoria del tiempo de inferencia mediante `time.perf_counter()` sobre
  `controller.compute()` y medición del uso de memoria.

RENDIMIENTO SIN CAMBIAR LA SEMÁNTICA (H-08):
- En el ciclo del algoritmo genético NO se reconstruye `ControlSystem` ni
  `ControlSystemSimulation` por individuo: la codificación pasa
  `build_control_system_graph=False` y el fitness evalúa con `compute_crisp`, que
  trabaja únicamente con arreglos numpy derivados del cromosoma.
- NO existe ninguna tabla interpolada de la superficie de control
  (`build_lookup_control_law` fue eliminada): el enunciado prohíbe "cualquier
  mecanismo de evaluación simplificada".
- La defuzzificación de `compute_crisp` replica línea por línea el procedimiento de
  `CrispValueCalculator.find_memberships` de scikit-fuzzy (universo remuestreado en
  los puntos de cruce, `np.union1d`, implicación min, agregación max y `defuzz`
  centroide), de modo que `compute_crisp` y `controller.compute()` coinciden para
  cualquier entrada interior del universo (verificado por `test_skfuzzy_equivalence`).
- Solo para la evaluación final (Fase 3) y las mediciones obligatorias de tiempo
  (`perf_counter` sobre `controller.compute()`, pág. 14 del enunciado) se construye
  el grafo completo de `skfuzzy.control`.
"""

import sys
import time
import tracemalloc
from typing import Dict, List, Tuple
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from skfuzzy.fuzzymath.fuzzy_ops import _interp_universe_fast, interp_membership

from src.chromosome import create_baseline_chromosome, decode_chromosome
from src.config import (
    COVERAGE_GRID_SIZE,
    DERROR_MAX,
    DERROR_MIN,
    ERROR_MAX,
    ERROR_MIN,
    LINGUISTIC_LABELS,
    UNIVERSE_RESOLUTION,
    VOLTAGE_MAX,
    VOLTAGE_MIN,
)


class MamdaniFuzzyController:
    """Encapsula el sistema difuso Mamdani en `skfuzzy.control` y su evaluación exacta."""

    def __init__(
        self,
        n_terms: int,
        chromosome: np.ndarray = None,
        use_automf_baseline: bool = False,
        build_control_system_graph: bool = True,
    ) -> None:
        self.n_terms = int(n_terms)
        self.labels = LINGUISTIC_LABELS[self.n_terms]
        self.use_automf_baseline = bool(use_automf_baseline)

        if chromosome is None:
            self.chromosome = create_baseline_chromosome(self.n_terms)
        else:
            self.chromosome = np.asarray(chromosome, dtype=float).copy()

        self.decoded = decode_chromosome(self.chromosome, self.n_terms)

        # Declaración obligatoria de Universos de Discurso (Parcial 2.pdf, pág. 13)
        self.error_universe = np.linspace(ERROR_MIN, ERROR_MAX, UNIVERSE_RESOLUTION)
        self.derror_universe = np.linspace(DERROR_MIN, DERROR_MAX, UNIVERSE_RESOLUTION)
        self.voltage_universe = np.linspace(
            VOLTAGE_MIN, VOLTAGE_MAX, UNIVERSE_RESOLUTION
        )

        self.error = ctrl.Antecedent(self.error_universe, "error")
        self.derror = ctrl.Antecedent(self.derror_universe, "derror")
        self.voltage = ctrl.Consequent(
            self.voltage_universe, "voltage", defuzzify_method="centroid"
        )

        if self.use_automf_baseline:
            # Fase 1 Obligatoria: generados explícitamente con automf (Parcial 2.pdf, pág. 8)
            self.error.automf(number=self.n_terms, names=self.labels)
            self.derror.automf(number=self.n_terms, names=self.labels)
            self.voltage.automf(number=self.n_terms, names=self.labels)
        else:
            for idx, label in enumerate(self.labels):
                self.error[label] = fuzz.trimf(
                    self.error.universe, self.decoded["error_mfs"][idx]
                )
                self.derror[label] = fuzz.trimf(
                    self.derror.universe, self.decoded["derror_mfs"][idx]
                )
                self.voltage[label] = fuzz.trimf(
                    self.voltage.universe, self.decoded["voltage_mfs"][idx]
                )

        # Construcción de las reglas activas en skfuzzy.control
        self.rules: List[ctrl.Rule] = []
        rule_active = self.decoded["rule_active"]
        rule_cons = self.decoded["rule_consequent"]

        if build_control_system_graph:
            for i in range(self.n_terms):
                for j in range(self.n_terms):
                    if rule_active[i, j]:
                        k = int(rule_cons[i, j])
                        rule = ctrl.Rule(
                            self.error[self.labels[i]] & self.derror[self.labels[j]],
                            self.voltage[self.labels[k]],
                        )
                        self.rules.append(rule)

            self.control_system = ctrl.ControlSystem(self.rules)
            self.simulation = ctrl.ControlSystemSimulation(self.control_system)
        else:
            self.control_system = None
            self.simulation = None

        # Pre-extraer las funciones de pertenencia desde los objetos Antecedent/Consequent de skfuzzy
        # para evaluación Mamdani idéntica a skfuzzy.control a precisión de máquina
        self._e_mfs = np.vstack(
            [self.error[label].mf for label in self.labels]
        )  # (N, 1000)
        self._de_mfs = np.vstack(
            [self.derror[label].mf for label in self.labels]
        )  # (N, 1000)
        self._v_mfs = np.vstack(
            [self.voltage[label].mf for label in self.labels]
        )  # (N, 1000)

        # Agrupación de reglas activas por término consecuente k in 0..N-1
        self._active_pairs_by_cons: List[Tuple[np.ndarray, np.ndarray]] = []
        for k in range(self.n_terms):
            ii, jj = np.where(rule_active & (rule_cons == k))
            self._active_pairs_by_cons.append((ii.astype(int), jj.astype(int)))

    @staticmethod
    def _interp_mfs(x: float, u_min: float, u_max: float, mfs: np.ndarray) -> np.ndarray:
        """Interpola linealmente sobre la malla de universo (idéntico a skfuzzy.interp_membership)."""
        n_pts = mfs.shape[1]
        # Acotar a [1, n_pts - 2] para evitar caída artificial a 0 en el nodo extremo donde a_0=u_min o c_{N-1}=u_max
        pos = float(np.clip((x - u_min) / (u_max - u_min) * (n_pts - 1), 1.0, n_pts - 2.0))
        idx = int(np.clip(np.floor(pos), 1, n_pts - 2))
        frac = float(np.clip(pos - idx, 0.0, 1.0))
        return (1.0 - frac) * mfs[:, idx] + frac * mfs[:, idx + 1]

    def compute_crisp(self, e_val: float, de_val: float) -> float:
        """Evalúa la inferencia Mamdani exacta (min-max-centroid con skfuzzy.defuzz).

        Replica el procedimiento de `skfuzzy.control.ControlSystemSimulation`:
        1. min(mu_e[i], mu_de[j]) para cada antecedente,
        2. max sobre las reglas que comparten consecuente k,
        3. remuestreo del universo del consecuente en los puntos donde cada MF
           corta el grado de activación (`_interp_universe_fast`), igual que
           `CrispValueCalculator.find_memberships` de scikit-fuzzy,
        4. implicación min, agregación max y defuzzificación centroide.

        Esto garantiza equivalencia de máquina con `controller.compute()` y evita
        la aproximación de defuzzificar solo sobre la malla uniforme de 1000 puntos.

        Convención de borde: `_interp_mfs` acota la posición de malla a los nodos
        interiores [1, n_pts-2]; así, cuando e/Δe saturan exactamente en los bordes
        del universo (saturación de entradas de la simulación), la evaluación no
        cae en el caso degenerado de scikit-fuzzy (todas las μ = 0 en el vértice
        exacto del universo -> `EmptyMembershipError`). La equivalencia con
        `controller.compute()` es exacta para toda entrada interior del universo,
        que es donde opera la simulación en lazo cerrado (ver
        `test_skfuzzy_equivalence`).
        """
        mu_e = self._interp_mfs(e_val, ERROR_MIN, ERROR_MAX, self._e_mfs)
        mu_de = self._interp_mfs(de_val, DERROR_MIN, DERROR_MAX, self._de_mfs)

        # Matriz de activación de antecedentes min(mu_e[i], mu_de[j])
        firing_matrix = np.minimum(mu_e[:, None], mu_de[None, :])

        # Grado de activación de cada consecuente k (max sobre sus reglas activas)
        active_terms = []
        for k, (ii, jj) in enumerate(self._active_pairs_by_cons):
            if len(ii) > 0:
                deg = float(np.max(firing_matrix[ii, jj]))
                if deg > 0.0:
                    active_terms.append((k, deg))

        if not active_terms:
            return 0.0

        # Remuestreo exacto del universo del consecuente (idéntico a skfuzzy.control)
        new_values = []
        for k, deg in active_terms:
            new_values.extend(
                _interp_universe_fast(
                    self.voltage_universe, self._v_mfs[k], deg
                ).tolist()
            )
        new_universe = np.union1d(self.voltage_universe, new_values)
        agg_mf = np.zeros_like(new_universe, dtype=np.float64)
        for k, deg in active_terms:
            upsampled_mf = interp_membership(
                self.voltage_universe, self._v_mfs[k], new_universe
            )
            np.maximum(agg_mf, np.minimum(deg, upsampled_mf), out=agg_mf)

        if np.sum(agg_mf) <= 1e-12:
            return 0.0

        return float(fuzz.defuzz(new_universe, agg_mf, "centroid"))

    def compute_with_skfuzzy_sim(self, e_val: float, de_val: float) -> float:
        """Ejecuta directamente `controller.compute()` sobre la instancia de `skfuzzy.control`."""
        du_e = (ERROR_MAX - ERROR_MIN) / (UNIVERSE_RESOLUTION - 1.0)
        du_de = (DERROR_MAX - DERROR_MIN) / (UNIVERSE_RESOLUTION - 1.0)
        self.simulation.input["error"] = float(
            np.clip(e_val, ERROR_MIN + du_e, ERROR_MAX - du_e)
        )
        self.simulation.input["derror"] = float(
            np.clip(de_val, DERROR_MIN + du_de, DERROR_MAX - du_de)
        )
        try:
            self.simulation.compute()
            return float(self.simulation.output["voltage"])
        except Exception:
            return 0.0

    def measure_rule_coverage(self, grid_size: int = COVERAGE_GRID_SIZE) -> Dict[str, float]:
        """H-13: cobertura de la base de reglas sobre la malla (e, Δe) — SOLO diagnóstico.

        Calcula la fracción de puntos de la malla (e, Δe) donde NINGUNA regla activa
        se dispara (todas las activaciones min(mu_e[i], mu_de[j]) con regla activa
        son nulas). Si ninguna regla dispara, `compute_crisp` devuelve 0.0 V
        silenciosamente ("zona muerta" del controlador), situación que puede aparecer
        al suprimir reglas y que no existía en el base line con todas las reglas.

        Detalles de fidelidad:
        - La interp de membresías replica exactamente el convenio de `_interp_mfs`
          usado por `compute_crisp` (acote a los nodos interiores [1, n_pts-2]),
          así que el diagnóstico es coherente con la inferencia usada en el lazo.
        - Es un DIAGNÓSTICO: la Ec. (12) NO se altera y no hay ninguna penalización
          asociada. Solo se reporta en el JSON de cada controlador final para que el
          reporte discuta la completitud de la base de reglas.
        """
        e_grid = np.linspace(ERROR_MIN, ERROR_MAX, grid_size)
        de_grid = np.linspace(DERROR_MIN, DERROR_MAX, grid_size)

        mu_e = self._mfs_on_grid(e_grid, ERROR_MIN, ERROR_MAX, self._e_mfs)   # (N, ge)
        mu_de = self._mfs_on_grid(de_grid, DERROR_MIN, DERROR_MAX, self._de_mfs)  # (N, gde)

        covered = np.zeros((grid_size, grid_size), dtype=bool)
        for ii, jj in self._active_pairs_by_cons:
            if len(ii) == 0:
                continue
            # Activación min(mu_e[i], mu_de[j]) por regla: (len(ii), ge, gde)
            act = np.minimum(mu_e[ii, :, None], mu_de[jj, None, :])
            covered |= np.any(act > 0.0, axis=0)

        uncovered_fraction = float(1.0 - covered.mean())
        return {
            "grid_size": int(grid_size),
            "covered_fraction": float(covered.mean()),
            "uncovered_fraction": uncovered_fraction,
            "uncovered_pct": 100.0 * uncovered_fraction,
            "num_active_rules": int(self.decoded["num_active_rules"]),
            "total_possible_rules": int(self.decoded["total_possible_rules"]),
        }

    def _mfs_on_grid(
        self, xs: np.ndarray, u_min: float, u_max: float, mfs: np.ndarray
    ) -> np.ndarray:
        """Interpola las N funciones de membresía sobre una malla de puntos, vectorizado.

        Réplica vectorizada de `_interp_mfs` (mismo convenio de nodos interiores
        [1, n_pts - 2] que `compute_crisp`) para la malla de diagnóstico.
        """
        n_pts = mfs.shape[1]
        pos = np.clip((xs - u_min) / (u_max - u_min) * (n_pts - 1), 1.0, n_pts - 2.0)
        idx = np.clip(np.floor(pos).astype(int), 1, n_pts - 2)
        frac = np.clip(pos - idx, 0.0, 1.0)
        return (1.0 - frac)[None, :] * mfs[:, idx] + frac[None, :] * mfs[:, idx + 1]

    def measure_inference_time_ms(self, n_evals: int = 50) -> float:
        """Mide el tiempo promedio de inferencia en milisegundos usando `time.perf_counter()`
        y `controller.compute()` según la especificación obligatoria de la página 14 de `Parcial 2.pdf`."""
        rng = np.random.default_rng(12345)
        e_samples = rng.uniform(ERROR_MIN * 0.9, ERROR_MAX * 0.9, size=n_evals)
        de_samples = rng.uniform(DERROR_MIN * 0.9, DERROR_MAX * 0.9, size=n_evals)

        controller = ctrl.ControlSystemSimulation(self.control_system, cache=False)
        timings: List[float] = []
        for e_s, de_s in zip(e_samples, de_samples):
            controller.input["error"] = float(e_s)
            controller.input["derror"] = float(de_s)
            start = time.perf_counter()
            controller.compute()
            end = time.perf_counter()
            inference_time = end - start
            timings.append(inference_time)

        return float(np.mean(timings) * 1000.0)


def measure_controller_memory_mb(
    n_terms: int, chromosome: np.ndarray = None, use_automf_baseline: bool = False
) -> float:
    """Mide el uso aproximado de memoria viva (en MB) asociado al controlador difuso en skfuzzy."""
    import gc

    gc.collect()
    tracemalloc.start()
    controller_obj = MamdaniFuzzyController(
        n_terms=n_terms,
        chromosome=chromosome,
        use_automf_baseline=use_automf_baseline,
        build_control_system_graph=True,
    )
    # Inicializar el estado interno de simulación con una inferencia
    controller_obj.compute_with_skfuzzy_sim(0.1, -0.05)
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del controller_obj
    return float(max(current_bytes, peak_bytes) / (1024.0 * 1024.0))
