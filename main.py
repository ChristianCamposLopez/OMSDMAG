"""Script maestro de ejecución reproducible del Parcial 2 de Computación Flexible.

Ejecuta de principio a fin:
1. Verificación del entorno y pruebas unitarias matemáticas.
2. Fase 1: Evaluación de los 3 Controladores Base (5, 7 y 9 términos con `automf`).
3. Fases 2-5: Optimización con PyGAD (5 ejecuciones independientes con semillas
   distintas para cada una de las 3 configuraciones = 15 corridas completas).
4. Cálculo de estadísticas (media ± desviación estándar y mejor individuo),
   generación de la Tabla Obligatoria de Resultados y las 8 figuras científicas.
"""

import argparse
import platform
import sys
import matplotlib
import numpy as np
import pygad
import scipy
import skfuzzy

from src.config import EXPERIMENT_SEEDS, NUM_GENERATIONS, SOL_PER_POP
from src.ga_optimizer import evaluate_baseline_controller, run_single_ga_experiment
from src.plotting_tables import generate_all_figures, summarize_experiments
from tests.test_verification import (
    test_chromosome_encoding_and_repair,
    test_equations_12_and_13,
    test_plant_and_reference,
    test_skfuzzy_equivalence,
)


def print_environment_info() -> None:
    print("=" * 78)
    print("ENTORNO DE EJECUCIÓN Y VERSIONES DE BIBLIOTECAS")
    print("=" * 78)
    print(f"Python       : {sys.version.split()[0]} ({platform.system()} {platform.release()})")
    print(f"numpy        : {np.__version__}")
    print(f"scipy        : {scipy.__version__}")
    print(f"scikit-fuzzy : {skfuzzy.__version__}")
    print(f"pygad        : {pygad.__version__}")
    print(f"matplotlib   : {matplotlib.__version__}")
    print("=" * 78)


def run_all_experiments(force_rerun: bool = False) -> dict:
    print_environment_info()

    print("\n[1/4] Ejecutando pruebas unitarias de verificación matemática y técnica...")
    test_plant_and_reference()
    test_equations_12_and_13()
    test_chromosome_encoding_and_repair()
    test_skfuzzy_equivalence()

    print("\n[2/4] Fase 1 Obligatoria: Evaluando Controladores Base (automf, sin GA)...")
    baselines = {}
    for n_terms in [5, 7, 9]:
        b_rec = evaluate_baseline_controller(n_terms)
        baselines[n_terms] = b_rec
        m = b_rec["metrics"]
        print(
            f"  -> Baseline {n_terms} términos ({b_rec['num_active_rules']} reglas): "
            f"Fitness={m['fitness']:.4f} | OS+={m['OS_pos']:.4f}, OS-={m['OS_neg']:.4f} | "
            f"SSE+={m['SSE_pos']:.4f}, SSE-={m['SSE_neg']:.4f} | "
            f"tr+={m['tr_pos']:.2f}s, tr-={m['tr_neg']:.2f}s | "
            f"ts+={m['ts_pos']:.2f}s, ts-={m['ts_neg']:.2f}s | "
            f"Inf={b_rec['inference_time_ms']:.3f}ms | Mem={b_rec['memory_mb']:.3f}MB"
        )

    print(
        f"\n[3/4] Fases 2-5 Obligatorias: Optimización con PyGAD "
        f"(sol_per_pop={SOL_PER_POP}, num_generations={NUM_GENERATIONS}, 5 semillas)..."
    )
    runs_by_terms = {5: [], 7: [], 9: []}
    for n_terms in [5, 7, 9]:
        print(f"\n--- Optimizando Controlador de {n_terms} términos lingüísticos ---")
        for run_idx, seed in enumerate(EXPERIMENT_SEEDS, start=1):
            rec = run_single_ga_experiment(
                n_terms=n_terms,
                seed=seed,
                sol_per_pop=SOL_PER_POP,
                num_generations=NUM_GENERATIONS,
                force_rerun=force_rerun,
            )
            runs_by_terms[n_terms].append(rec)
            m = rec["metrics"]
            print(
                f"  Corrida {run_idx}/5 (semilla={seed:4d}): "
                f"Fitness={m['fitness']:.4f} | OS+={m['OS_pos']:.4f}, OS-={m['OS_neg']:.4f} | "
                f"SSE+={m['SSE_pos']:.4f}, SSE-={m['SSE_neg']:.4f} | "
                f"tr+={m['tr_pos']:.2f}s, tr-={m['tr_neg']:.2f}s | "
                f"ts+={m['ts_pos']:.2f}s, ts-={m['ts_neg']:.2f}s | "
                f"Reglas={rec['num_active_rules']}/{rec['total_possible_rules']} | "
                f"Opt={rec['optimization_time_s']:.2f}s | Inf={rec['inference_time_ms']:.3f}ms | "
                f"Mem={rec['memory_mb']:.3f}MB"
            )

    print("\n[4/4] Generando tablas estadísticas y figuras científicas...")
    summary = summarize_experiments(baselines, runs_by_terms)
    figs = generate_all_figures(baselines, runs_by_terms, summary)
    print(f"  -> {len(figs)} figuras guardadas en 'results/figures/'.")

    print("\n" + "=" * 78)
    with open("results/tables/tabla_obligatoria_resultados.md", "r", encoding="utf-8") as f:
        print(f.read())
    print("=" * 78)

    return {
        "baselines": baselines,
        "runs_by_terms": runs_by_terms,
        "summary": summary,
        "figures": figs,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ejecución completa del proyecto Parcial 2 de Computación Flexible"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar la re-ejecución de las 15 corridas de PyGAD aunque existan en disco.",
    )
    args = parser.parse_args()
    run_all_experiments(force_rerun=args.force)

