"""Módulo de optimización evolutiva con PyGAD y ejecución del protocolo experimental.

Implementa las 5 fases obligatorias de la Parte 3 de `Parcial 2.pdf` (págs. 8-10, 14):
- Fase 1: Evaluación de los tres Controladores Base (5, 7 y 9 términos con `automf`).
- Fase 2: Optimización mediante `pygad.GA` (mínimo 20 individuos y 30 generaciones).
- Fase 3: Selección del mejor individuo por configuración usando exclusivamente la Ec. (12).
- Fase 4: Evaluación cuantitativa del costo computacional (tiempo de optimización,
  tiempo promedio de inferencia con `perf_counter`, número de genes, reglas activas y memoria).
- Fase 5: Repetibilidad experimental (5 ejecuciones independientes con semillas distintas).
"""

import json
import os
import random
import time
from typing import Dict, List
import numpy as np
import pygad

from src.chromosome import (
    create_baseline_chromosome,
    decode_chromosome,
    get_gene_space,
    get_num_genes,
)
from src.config import (
    CROSSOVER_PROBABILITY,
    CROSSOVER_TYPE,
    DERROR_MAX,
    DERROR_MIN,
    ERROR_MAX,
    ERROR_MIN,
    EXPERIMENT_SEEDS,
    KEEP_ELITISM,
    MUTATION_PROBABILITY,
    MUTATION_TYPE,
    NUM_GENERATIONS,
    NUM_PARENTS_MATING,
    SOL_PER_POP,
    VOLTAGE_MAX,
    VOLTAGE_MIN,
)
from src.fuzzy_controller import MamdaniFuzzyController, measure_controller_memory_mb
from src.metrics_fitness import evaluate_controller_response
from src.plant_sim import ClosedLoopPlantSimulator


def generate_initial_population(
    n_terms: int, sol_per_pop: int, seed: int
) -> np.ndarray:
    """Genera la población inicial diversa y factible para una semilla aleatoria dada."""
    rng = np.random.default_rng(seed)
    n_genes = get_num_genes(n_terms)
    base = create_baseline_chromosome(n_terms)
    pop = np.zeros((sol_per_pop, n_genes), dtype=float)

    block = 3 * n_terms
    n_rules = n_terms ** 2
    act_start = 3 * block
    cons_start = act_start + n_rules

    for idx in range(sol_per_pop):
        indiv = base.copy()

        # Factores de concentración hacia el origen (mayor ganancia cerca de error=0)
        # que permiten al GA explorar respuestas más rápidas sin perder estabilidad
        alpha_e = float(rng.uniform(0.35, 1.15))
        alpha_de = float(rng.uniform(0.40, 1.20))
        alpha_v = float(rng.uniform(0.55, 1.35))

        for var_idx, (u_min, u_max, alpha) in enumerate(
            [
                (ERROR_MIN, ERROR_MAX, alpha_e),
                (DERROR_MIN, DERROR_MAX, alpha_de),
                (VOLTAGE_MIN, VOLTAGE_MAX, alpha_v),
            ]
        ):
            offset = var_idx * block
            # Distribución no lineal simétrica/asimétrica de centros en [-1, 1]
            u_norm = np.linspace(-1.0, 1.0, n_terms)
            warped = np.sign(u_norm) * (np.abs(u_norm) ** alpha)
            jitter = rng.normal(0.0, 0.08, size=n_terms)
            jitter[0] = 0.0
            jitter[-1] = 0.0
            warped = np.clip(warped + jitter, -1.0, 1.0)
            warped = np.sort(warped)
            centers = u_min + (warped + 1.0) * 0.5 * (u_max - u_min)
            indiv[offset : offset + n_terms] = centers

            # Anchuras y solapamientos en [0.30, 1.70]
            indiv[offset + n_terms : offset + block] = rng.uniform(
                0.35, 1.65, size=2 * n_terms
            )

        # Para las variables de salida (voltage), ensanchar los conjuntos extremos en algunos individuos
        # para desplazar sus centroides hacia +-8.18 V y acelerar el tiempo de subida
        if idx % 2 == 0:
            v_off = 2 * block
            indiv[v_off + n_terms] = float(rng.uniform(1.2, 1.75))
            indiv[v_off + 2 * n_terms - 1] = float(rng.uniform(1.2, 1.75))

        # Activación de reglas: tasa de activación variable entre 55% y 95%
        keep_prob = float(rng.uniform(0.55, 0.95))
        active_vals = np.where(
            rng.random(n_rules) < keep_prob,
            rng.uniform(0.52, 1.0, size=n_rules),
            rng.uniform(0.0, 0.48, size=n_rules),
        )
        # Mantener activa la regla de equilibrio central (ZE, ZE)
        mid_rule = (n_terms // 2) * n_terms + (n_terms // 2)
        active_vals[mid_rule] = 0.95
        indiv[act_start:cons_start] = active_vals

        # Consecuentes: base PD con mutaciones locales hacia términos más enérgicos
        base_cons = base[cons_start : cons_start + n_rules].copy()
        if idx > 0:
            # Empujar consecuentes hacia los extremos en parte de la población para reducir tr
            gain_shift = np.sign(base_cons - (n_terms - 1) / 2.0) * rng.choice(
                [0.0, 1.0], size=n_rules, p=[0.45, 0.55]
            )
            noise_shift = rng.choice([-1.0, 0.0, 1.0], size=n_rules, p=[0.12, 0.76, 0.12])
            new_cons = np.clip(base_cons + gain_shift + noise_shift, 0.0, float(n_terms - 1))
            new_cons[mid_rule] = float(n_terms // 2)
            indiv[cons_start : cons_start + n_rules] = new_cons

        pop[idx] = indiv

    return pop


def evaluate_baseline_controller(
    n_terms: int, results_dir: str = "results/baselines"
) -> Dict[str, object]:
    """Ejecuta la Fase 1 Obligatoria: evaluación del controlador Baseline (`automf`) sin GA."""
    os.makedirs(results_dir, exist_ok=True)
    simulator = ClosedLoopPlantSimulator()

    ctrl_obj = MamdaniFuzzyController(
        n_terms=n_terms,
        chromosome=None,
        use_automf_baseline=True,
        build_control_system_graph=True,
    )

    # Simulación completa de 200 s usando la inferencia Mamdani exacta punto a punto
    sim_res = simulator.simulate(ctrl_obj.compute_crisp)
    metrics = evaluate_controller_response(sim_res["t"], sim_res["theta"])

    # Medición obligatoria de tiempo de inferencia (ms) y memoria (MB)
    inf_time_ms = ctrl_obj.measure_inference_time_ms(n_evals=50)
    mem_mb = measure_controller_memory_mb(
        n_terms=n_terms, chromosome=None, use_automf_baseline=True
    )

    record = {
        "n_terms": n_terms,
        "type": "baseline_automf",
        "num_genes": get_num_genes(n_terms),
        "num_active_rules": ctrl_obj.decoded["num_active_rules"],
        "total_possible_rules": ctrl_obj.decoded["total_possible_rules"],
        "active_rules_list": ctrl_obj.decoded["active_rules_list"],
        "inference_time_ms": inf_time_ms,
        "memory_mb": mem_mb,
        "optimization_time_s": 0.0,
        "metrics": metrics,
        "chromosome": ctrl_obj.chromosome.tolist(),
        "decoded_mfs": {
            "error_mfs": ctrl_obj.decoded["error_mfs"].tolist(),
            "derror_mfs": ctrl_obj.decoded["derror_mfs"].tolist(),
            "voltage_mfs": ctrl_obj.decoded["voltage_mfs"].tolist(),
            "rule_active": ctrl_obj.decoded["rule_active"].astype(int).tolist(),
            "rule_consequent": ctrl_obj.decoded["rule_consequent"].tolist(),
        },
        "trajectory": {
            "t": sim_res["t"].tolist(),
            "r": sim_res["r"].tolist(),
            "u": sim_res["u"].tolist(),
            "theta": sim_res["theta"].tolist(),
            "e": sim_res["e"].tolist(),
            "de": sim_res["de"].tolist(),
        },
    }

    out_path = os.path.join(results_dir, f"baseline_{n_terms}terms.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    return record


def run_single_ga_experiment(
    n_terms: int,
    seed: int,
    sol_per_pop: int = SOL_PER_POP,
    num_generations: int = NUM_GENERATIONS,
    results_dir: str = "results/runs",
    force_rerun: bool = False,
) -> Dict[str, object]:
    """Ejecuta una corrida independiente de PyGAD para `n_terms` y `seed`."""
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(
        results_dir, f"controller_{n_terms}terms_seed_{seed}.json"
    )

    if os.path.exists(out_path) and not force_rerun:
        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fijar semillas para reproducibilidad
    np.random.seed(seed)
    random.seed(seed)

    simulator = ClosedLoopPlantSimulator()
    gene_space = get_gene_space(n_terms)
    init_pop = generate_initial_population(n_terms, sol_per_pop, seed)

    # Cache por cromosoma redondeado para no repetir simulaciones idénticas (elitismo)
    eval_cache: Dict[bytes, float] = {}

    def fitness_func(ga_instance, solution, solution_idx) -> float:
        key = np.round(solution, 6).tobytes()
        if key in eval_cache:
            return eval_cache[key]

        # 1. Construir el sistema difuso y decodificar/reparar el cromosoma
        ctrl_fast = MamdaniFuzzyController(
            n_terms=n_terms,
            chromosome=solution,
            use_automf_baseline=False,
            build_control_system_graph=False,
        )
        law = ctrl_fast.build_lookup_control_law(grid_size=65)

        # 2. Simular los 200 segundos completos con scipy.signal.lsim
        sim_out = simulator.simulate(law)

        # 3, 4 y 5. Calcular métricas de rendimiento, penalizaciones q y función fitness (Ec. 12 y 13)
        res = evaluate_controller_response(sim_out["t"], sim_out["theta"])
        fit_val = float(res["fitness"]) - float(ctrl_fast.decoded["repair_penalty"])
        fit_val = max(1e-6, fit_val)

        eval_cache[key] = fit_val
        return fit_val

    ga_instance = pygad.GA(
        num_generations=num_generations,
        num_parents_mating=NUM_PARENTS_MATING,
        fitness_func=fitness_func,
        initial_population=init_pop,
        gene_space=gene_space,
        parent_selection_type="tournament",
        K_tournament=3,
        keep_elitism=KEEP_ELITISM,
        crossover_type=CROSSOVER_TYPE,
        crossover_probability=CROSSOVER_PROBABILITY,
        mutation_type=MUTATION_TYPE,
        mutation_probability=MUTATION_PROBABILITY,
        mutation_by_replacement=False,
        random_mutation_min_val=-0.25,
        random_mutation_max_val=0.25,
        random_seed=int(seed),
        suppress_warnings=True,
    )

    # Medición obligatoria del tiempo de optimización (Parcial 2.pdf, pág. 14)
    start = time.time()
    ga_instance.run()
    end = time.time()
    optimization_time = float(end - start)

    best_solution, best_fitness_ga, _ = ga_instance.best_solution()

    # Reconstruir el controlador ganador completo con grafo skfuzzy.control
    best_ctrl = MamdaniFuzzyController(
        n_terms=n_terms,
        chromosome=best_solution,
        use_automf_baseline=False,
        build_control_system_graph=True,
    )

    # Evaluación final exacta sobre los 200 s completos
    final_sim = simulator.simulate(best_ctrl.compute_crisp)
    final_metrics = evaluate_controller_response(final_sim["t"], final_sim["theta"])

    # Medición obligatoria del tiempo de inferencia con time.perf_counter() y controller.compute()
    inference_time_ms = best_ctrl.measure_inference_time_ms(n_evals=50)
    memory_mb = measure_controller_memory_mb(
        n_terms=n_terms, chromosome=best_solution, use_automf_baseline=False
    )

    # Historial de convergencia por generación (incluyendo generación 0 + 30 generaciones)
    fitness_history = [float(v) for v in ga_instance.best_solutions_fitness]

    record = {
        "n_terms": n_terms,
        "seed": int(seed),
        "sol_per_pop": int(sol_per_pop),
        "num_generations": int(num_generations),
        "num_genes": get_num_genes(n_terms),
        "optimization_time_s": optimization_time,
        "inference_time_ms": inference_time_ms,
        "memory_mb": memory_mb,
        "fitness_ga_lookup": float(best_fitness_ga),
        "fitness_exact": float(final_metrics["fitness"]),
        "metrics": final_metrics,
        "num_active_rules": best_ctrl.decoded["num_active_rules"],
        "total_possible_rules": best_ctrl.decoded["total_possible_rules"],
        "active_rules_list": best_ctrl.decoded["active_rules_list"],
        "fitness_history": fitness_history,
        "best_chromosome": best_solution.tolist(),
        "decoded_mfs": {
            "error_mfs": best_ctrl.decoded["error_mfs"].tolist(),
            "derror_mfs": best_ctrl.decoded["derror_mfs"].tolist(),
            "voltage_mfs": best_ctrl.decoded["voltage_mfs"].tolist(),
            "rule_active": best_ctrl.decoded["rule_active"].astype(int).tolist(),
            "rule_consequent": best_ctrl.decoded["rule_consequent"].tolist(),
        },
        "trajectory": {
            "t": final_sim["t"].tolist(),
            "r": final_sim["r"].tolist(),
            "u": final_sim["u"].tolist(),
            "theta": final_sim["theta"].tolist(),
            "e": final_sim["e"].tolist(),
            "de": final_sim["de"].tolist(),
        },
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    return record

