"""Suite de pruebas unitarias para verificar el cumplimiento matemático y técnico.

Verifica:
1. Planta G(s) y señal de referencia cuadrada de 200 s.
2. Ecuaciones (12) y (13): casos ideales, penalización q de falso tiempo de crecimiento y casos extremos.
3. Codificación genética, tamaños de cromosoma (95, 161, 243 genes) y reparación de funciones de membresía.
4. Equivalencia exacta entre `skfuzzy.control.ControlSystemSimulation.compute()` y el evaluador Mamdani.
5. Evaluación completa de los 3 controladores Baseline (5, 7 y 9 términos con `automf`).
"""

import numpy as np

from src.chromosome import (
    create_baseline_chromosome,
    decode_chromosome,
    get_gene_space,
    get_num_genes,
)
from src.config import (
    DERROR_MAX,
    DERROR_MIN,
    ERROR_MAX,
    ERROR_MIN,
    TR0,
    TS0,
    VOLTAGE_MAX,
    VOLTAGE_MIN,
)
from src.fuzzy_controller import MamdaniFuzzyController
from src.metrics_fitness import compute_penalty_factor_q, evaluate_controller_response
from src.plant_sim import ClosedLoopPlantSimulator, create_plant, create_time_and_reference


def test_plant_and_reference() -> None:
    G = create_plant()
    assert np.allclose(G.num, [0.5])
    assert np.allclose(G.den, [1.0, 13.6667, 23.3487, 0.0])

    t, r = create_time_and_reference()
    assert np.isclose(t[0], 0.0)
    assert np.isclose(t[-1], 200.0)
    assert np.all(np.isin(r, [-1.0, 1.0]))
    # Verificar signos en cada semiperíodo de 50 s
    assert np.all(r[(t >= 0.0) & (t < 50.0)] == 1.0)
    assert np.all(r[(t > 50.0) & (t < 100.0)] == -1.0)
    assert np.all(r[(t > 100.0) & (t < 150.0)] == 1.0)
    assert np.all(r[(t > 150.0) & (t <= 200.0)] == -1.0)
    print("[OK] test_plant_and_reference superado.")


def test_equations_12_and_13() -> None:
    t, r = create_time_and_reference()

    # Caso 1: Respuesta ideal sintética con tr = 9 s, ts = 13 s, OS = 0, SSE = 0
    theta_ideal = np.zeros_like(t)
    for t0, r_ini, r_fin in [(0.0, 0.0, 1.0), (50.0, 1.0, -1.0), (100.0, -1.0, 1.0), (150.0, 1.0, -1.0)]:
        mask = (t >= t0) & (t < t0 + 50.0) if t0 < 150.0 else (t >= t0) & (t <= t0 + 50.0)
        tau = t[mask] - t0
        # tau=0 -> 10% (prog=0.10), tau=9 -> 90% (prog=0.90), tau=13 -> banda 0.05 rad (prog=0.975 -> 1.0)
        prog = np.interp(tau, [0.0, 9.0, 12.95, 13.0, 50.0], [0.10, 0.90, 0.974, 1.0, 1.0])
        theta_ideal[mask] = r_ini + prog * (r_fin - r_ini)

    res_ideal = evaluate_controller_response(t, theta_ideal)
    assert np.isclose(res_ideal["q_pos"], 1.0, atol=0.15)
    assert np.isclose(res_ideal["OS_pos"], 0.0, atol=1e-6)
    assert np.isclose(res_ideal["SSE_pos"], 0.0, atol=1e-3)
    assert np.isclose(res_ideal["tr_pos"], TR0, atol=0.15)
    assert np.isclose(res_ideal["ts_pos"], TS0, atol=0.15)
    assert res_ideal["fitness"] > 0.96, f"Fitness ideal esperado ~1.0, obtenido {res_ideal['fitness']}"

    # Caso 2: Falso tiempo de crecimiento (alcanza solo el 25% de la excursión)
    h_partial = np.linspace(-1.0, -0.5, 100)  # Excursión de 0.5 rad en vez de 2.0 rad
    q_partial = compute_penalty_factor_q(h_partial, h0_min=-1.0, h0_max=1.0)
    assert np.isclose(q_partial, 4.0, atol=1e-4), f"Se esperaba q=4.0, obtenido {q_partial}"

    # Caso 3: Respuesta plana degenerada theta(t) = 0 (cálculo manual exacto de Ec. 12 y 13)
    theta_zero = np.zeros_like(t)
    res_zero = evaluate_controller_response(t, theta_zero)
    assert np.isfinite(res_zero["fitness"])
    assert res_zero["q_pos"] >= 1e5
    expected_zero_fitness = 2.0 * 0.125 * (1.0 / (1.0 + 0.0) + 1.0 / (1.0 + 1.0) + 0.0 + 13.0 / 50.0)
    assert np.isclose(res_zero["fitness"], expected_zero_fitness, atol=1e-3)
    print("[OK] test_equations_12_and_13 superado.")


def test_chromosome_encoding_and_repair() -> None:
    expected_counts = {5: 95, 7: 161, 9: 243}
    rng = np.random.default_rng(2026)

    for n_terms, expected_len in expected_counts.items():
        assert get_num_genes(n_terms) == expected_len
        space = get_gene_space(n_terms)
        assert len(space) == expected_len

        # Probar 25 cromosomas con valores extremos/desordenados/fuera de rango
        for _ in range(25):
            random_chrom = rng.uniform(-15.0, 15.0, size=expected_len)
            # Forzar un caso con todas las reglas apagadas
            if _ == 0:
                random_chrom[:] = 0.0
            decoded = decode_chromosome(random_chrom, n_terms)

            for mfs, u_min, u_max in [
                (decoded["error_mfs"], ERROR_MIN, ERROR_MAX),
                (decoded["derror_mfs"], DERROR_MIN, DERROR_MAX),
                (decoded["voltage_mfs"], VOLTAGE_MIN, VOLTAGE_MAX),
            ]:
                assert mfs.shape == (n_terms, 3)
                assert np.all(mfs[:, 0] >= u_min - 1e-9)
                assert np.all(mfs[:, 2] <= u_max + 1e-9)
                assert np.all(mfs[:, 0] <= mfs[:, 1] + 1e-9)
                assert np.all(mfs[:, 1] <= mfs[:, 2] + 1e-9)
                assert np.all(mfs[:, 2] > mfs[:, 0])  # Sin funciones degeneradas de anchura 0

            assert decoded["num_active_rules"] >= 1
    print("[OK] test_chromosome_encoding_and_repair superado.")


def test_skfuzzy_equivalence() -> None:
    for n_terms in [5, 7, 9]:
        ctrl_obj = MamdaniFuzzyController(n_terms=n_terms, use_automf_baseline=True)
        rng = np.random.default_rng(n_terms)
        for _ in range(15):
            e_val = float(rng.uniform(ERROR_MIN * 0.95, ERROR_MAX * 0.95))
            de_val = float(rng.uniform(DERROR_MIN * 0.95, DERROR_MAX * 0.95))
            v_skf = ctrl_obj.compute_with_skfuzzy_sim(e_val, de_val)
            v_exact = ctrl_obj.compute_crisp(e_val, de_val)
            assert np.isclose(
                v_skf, v_exact, atol=1e-4
            ), f"Discrepancia para N={n_terms}: skfuzzy={v_skf} vs exact={v_exact}"
    print("[OK] test_skfuzzy_equivalence superado (precisión < 1e-4 V).")


if __name__ == "__main__":
    test_plant_and_reference()
    test_equations_12_and_13()
    test_chromosome_encoding_and_repair()
    test_skfuzzy_equivalence()
    print("=== TODAS LAS PRUEBAS UNITARIAS SUPERADAS EXITOSAMENTE ===")
