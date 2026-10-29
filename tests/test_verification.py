"""Suite de pruebas unitarias para verificar el cumplimiento matemático y técnico.

Verifica:
1. Planta G(s), señal de referencia cuadrada de 200 s y simulación exclusiva con `scipy.signal.lsim`.
2. Ecuaciones (12) y (13): OS en porcentaje (%), penalización q >= 1.0 cuando el estado estable
   queda por debajo de la referencia ([min(h), max(h)] <= [min(h0), max(h0)]), y casos extremos.
3. Codificación genética, tamaños de cromosoma (95, 161, 243 genes), traslape entre conjuntos y
   orden estricto a < b < c en todas las funciones de membresía triangulares.
4. Equivalencia exacta entre `skfuzzy.control.ControlSystemSimulation.compute()` y el evaluador Mamdani.
"""

import inspect
import numpy as np

import src.plant_sim as plant_sim_mod
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

    # Verificar que plant_sim usa estrictamente scipy.signal.lsim sin expm
    src_code = inspect.getsource(plant_sim_mod)
    assert "expm" not in src_code, "No debe utilizarse expm ni discretización manual."
    assert "lsim(" in src_code, "Debe utilizarse estrictamente scipy.signal.lsim."

    t, r = create_time_and_reference()
    assert np.isclose(t[0], 0.0)
    assert np.isclose(t[-1], 200.0)
    assert np.all(np.isin(r, [-1.0, 1.0]))
    # Verificar signos en cada semiperíodo de 50 s
    assert np.all(r[(t >= 0.0) & (t < 50.0)] == 1.0)
    assert np.all(r[(t > 50.0) & (t < 100.0)] == -1.0)
    assert np.all(r[(t > 100.0) & (t < 150.0)] == 1.0)
    assert np.all(r[(t > 150.0) & (t <= 200.0)] == -1.0)
    print("[OK] test_plant_and_reference (con verificación estricta de lsim) superado.")


def test_equations_12_and_13() -> None:
    t, r = create_time_and_reference()

    # Caso 1: Respuesta ideal sintética con tr = 9 s, ts = 13 s, OS = 0%, SSE = 0 rad
    theta_ideal = np.zeros_like(t)
    for t0, r_ini, r_fin in [
        (0.0, 0.0, 1.0),
        (50.0, 1.0, -1.0),
        (100.0, -1.0, 1.0),
        (150.0, 1.0, -1.0),
    ]:
        mask = (
            (t >= t0) & (t < t0 + 50.0)
            if t0 < 150.0
            else (t >= t0) & (t <= t0 + 50.0)
        )
        tau = t[mask] - t0
        prog = np.interp(
            tau, [0.0, 0.1, 9.1, 12.90, 13.0, 50.0], [0.0, 0.10, 0.90, 0.974, 1.0, 1.0]
        )
        theta_ideal[mask] = r_ini + prog * (r_fin - r_ini)

    res_ideal = evaluate_controller_response(t, theta_ideal)
    assert np.isclose(res_ideal["q_pos"], 1.0, atol=1e-6)
    assert np.isclose(res_ideal["OS_pos"], 0.0, atol=1e-6)
    assert np.isclose(res_ideal["SSE_pos"], 0.0, atol=1e-3)
    assert np.isclose(res_ideal["tr_pos"], TR0, atol=0.20)
    assert np.isclose(res_ideal["ts_pos"], TS0, atol=0.20)
    assert (
        res_ideal["fitness"] > 0.96
    ), f"Fitness ideal esperado ~1.0, obtenido {res_ideal['fitness']}"

    # Verificar que OS se calcula como porcentaje (%): un exceso de 0.05 rad sobre 1.0 rad es 5.0%
    theta_os = theta_ideal.copy()
    mask_peak = (t >= 114.0) & (t <= 115.0)
    theta_os[mask_peak] = 1.05
    res_os = evaluate_controller_response(t, theta_os)
    assert np.isclose(
        res_os["OS_pos"], 5.0, atol=1e-4
    ), f"OS esperado 5.0%, obtenido {res_os['OS_pos']}%"

    # Caso 2: Falso tiempo de crecimiento (alcanza solo el 25% de la excursión: [-1.0, -0.5])
    h_partial = np.linspace(-1.0, -0.5, 100)
    q_partial = compute_penalty_factor_q(h_partial, h0_min=-1.0, h0_max=1.0)
    assert np.isclose(
        q_partial, 4.0, atol=1e-4
    ), f"Se esperaba q=4.0 (> 1.0), obtenido {q_partial}"

    # Caso 3: Respuesta plana degenerada theta(t) = 0
    theta_zero = np.zeros_like(t)
    res_zero = evaluate_controller_response(t, theta_zero)
    assert np.isfinite(res_zero["fitness"])
    assert res_zero["q_pos"] >= 1e5
    expected_zero_fitness = (
        2.0
        * 0.125
        * (1.0 / (1.0 + 0.0) + 1.0 / (1.0 + 1.0) + 0.0 + 13.0 / 50.0)
    )
    assert np.isclose(res_zero["fitness"], expected_zero_fitness, atol=1e-3)
    print("[OK] test_equations_12_and_13 (con OS en % y q >= 1.0 según Ec. 13) superado.")


def test_chromosome_encoding_and_repair() -> None:
    expected_counts = {5: 95, 7: 161, 9: 243}
    rng = np.random.default_rng(2026)

    for n_terms, expected_len in expected_counts.items():
        assert get_num_genes(n_terms) == expected_len
        space = get_gene_space(n_terms)
        assert len(space) == expected_len

        # Verificar también el cromosoma base
        base_dec = decode_chromosome(create_baseline_chromosome(n_terms), n_terms)
        for mfs in [base_dec["error_mfs"], base_dec["derror_mfs"], base_dec["voltage_mfs"]]:
            assert np.all(mfs[:, 0] < mfs[:, 1]), "Debe cumplirse estrictamente a < b"
            assert np.all(mfs[:, 1] < mfs[:, 2]), "Debe cumplirse estrictamente b < c"

        # Probar 25 cromosomas con valores extremos/desordenados/fuera de rango
        for idx in range(25):
            random_chrom = rng.uniform(-15.0, 15.0, size=expected_len)
            if idx == 0:
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
                # Orden estricto obligatorio a < b < c
                assert np.all(mfs[:, 0] < mfs[:, 1]), f"Violación de a < b: {mfs}"
                assert np.all(mfs[:, 1] < mfs[:, 2]), f"Violación de b < c: {mfs}"
                # Centros estrictamente crecientes y traslape entre conjuntos vecinos
                assert np.all(np.diff(mfs[:, 1]) > 0)
                assert np.all(mfs[:-1, 2] > mfs[1:, 0]), "Debe existir traslape entre conjuntos vecinos"

            assert decoded["num_active_rules"] >= 1
    print("[OK] test_chromosome_encoding_and_repair (con orden estricto a < b < c y traslapes) superado.")


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
