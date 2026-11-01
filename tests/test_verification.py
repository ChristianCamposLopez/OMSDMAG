"""Suite de pruebas unitarias para verificar el cumplimiento matemático y técnico.

Verifica:
1. Planta G(s), señal de referencia cuadrada de 200 s y simulación exclusiva con `scipy.signal.lsim`,
   incluyendo la consistencia entre el lazo paso a paso y la llamada global final.
2. Ecuaciones (12) y (13): OS en porcentaje (%), factor q literal con q >= 1.0, y casos extremos.
3. Codificación genética, tamaños de cromosoma (95, 161, 243 genes), traslape entre conjuntos y
   orden estricto a < b < c en todas las funciones de membresía triangulares.
4. Equivalencia exacta entre `skfuzzy.control.ControlSystemSimulation.compute()` y el evaluador
   Mamdani, tanto para controladores `automf` como para cromosomas optimizados y todo el rango.
5. Que el algoritmo genético evalúe cada individuo con la inferencia exacta (sin tablas sustitutas)
   y que tr0/ts0 no sean parámetros sobrescribibles.
6. Consistencia del lazo frente al `lsim` único con el mismo modo de interpolación (H-02),
   diagnosticada con varias leyes de control.
7. Cobertura de reglas (H-13: baseline `automf` cubre toda la malla; un controlador con una sola
   regla deja zonas muertas) y diagnóstico de saturación de entradas (H-09).
"""

import inspect
import numpy as np

import src.ga_optimizer as ga_optimizer_mod
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
from src.metrics_fitness import (
    compute_penalty_factor_q,
    evaluate_controller_response,
)
from src.plant_sim import (
    ClosedLoopPlantSimulator,
    create_plant,
    create_time_and_reference,
)


def test_plant_and_reference() -> None:
    G = create_plant()
    assert np.allclose(G.num, [0.5])
    assert np.allclose(G.den, [1.0, 13.6667, 23.3487, 0.0])

    # Verificar que plant_sim usa estrictamente scipy.signal.lsim sin integradores externos
    src_code = inspect.getsource(plant_sim_mod)
    for forbidden in ("expm", "odeint", "solve_ivp", "ode("):
        assert forbidden not in src_code, f"No debe utilizarse {forbidden}."
    assert "lsim(" in src_code, "Debe utilizarse estrictamente scipy.signal.lsim."

    t, r = create_time_and_reference()
    assert np.isclose(t[0], 0.0)
    assert np.isclose(t[-1], 200.0)
    assert np.all(np.isin(r, [-1.0, 1.0]))
    # Verificar signos en cada semiperíodo de 50 s, incluido el instante final
    assert np.all(r[(t >= 0.0) & (t < 50.0)] == 1.0)
    assert np.all(r[(t >= 50.0) & (t < 100.0)] == -1.0)
    assert np.all(r[(t >= 100.0) & (t < 150.0)] == 1.0)
    assert np.all(r[(t >= 150.0) & (t <= 200.0)] == -1.0)
    assert r[-1] == -1.0, "El instante final debe permanecer en el último semiperíodo."

    # Consistencia H-02: la trayectoria del lazo y la del lsim global deben coincidir
    # (ver test dedicado test_lsim_loop_final_consistency con varias leyes).
    simulator = ClosedLoopPlantSimulator()
    sim = simulator.simulate(lambda e, de: -2.0 * e - 0.2 * de)
    assert sim["lsim_consistency_error"] < 1e-9, (
        "La trayectoria evaluada no coincide con la generada por el lazo: "
        f"{sim['lsim_consistency_error']:.3e}"
    )
    print("[OK] test_plant_and_reference (lsim ZOH consistente y referencia explícita) superado.")


def test_lsim_loop_final_consistency() -> None:
    """H-02 (Fase P1): comparación explícita de ambas trayectorias.

    Para varias leyes de control —incluida una bang-bang que produce conmutaciones
    agresivas— debe cumplirse:

        theta_evaluada = lsim(G, U=u, T=t, X0=x0, interp=False)
                              == theta del lazo paso a paso (mismo modo ZOH)

    La igualdad debe ser exacta (tolerancia 1e-9) porque scipy 1.18.1 implementa el
    modo interp=False de lsim avanzando xout[i] = xout[i-1] @ Ad + U[i-1] @ Bd: mantiene
    la entrada al inicio de cada intervalo, idéntico al lazo per-intervalo. Si la
    implementación del lazo cambiara de modo de interpolación, este test debe fallar
    hasta que se alineen las dos llamadas.
    """
    simulator = ClosedLoopPlantSimulator()

    control_laws = {
        "zero (u=0)": lambda e, de: 0.0,
        "PD lineal": lambda e, de: -2.0 * e - 0.2 * de,
        "bang-bang saturada (±8.18 V)": lambda e, de: 8.18 if e > 0 else -8.18,
        "constante 1.5 V": lambda e, de: 1.5,
    }

    for law_name, law in control_laws.items():
        sim = simulator.simulate(law)
        max_diff = float(np.max(np.abs(sim["theta"] - sim["theta_loop"])))

        # 1) Las dos trayectorias (lazo y lsim único) son la misma
        assert np.allclose(
            sim["theta"], sim["theta_loop"], atol=1e-9
        ), (
            f"Ley '{law_name}': theta del lsim global difiere del lazo "
            f"(max |diff| = {max_diff:.3e}); revisar el modo de interpolación."
        )

        # 2) El campo de diagnóstico reporta exactamente ese máximo
        assert np.isclose(
            sim["lsim_consistency_error"], max_diff, atol=1e-15
        ), f"Ley '{law_name}': lsim_consistency_error inconsistente."

        # 3) Sanidad de la convención del reporte: e = r - theta en el primer instante
        assert np.isclose(
            sim["e"][0], sim["r"][0] - sim["theta"][0], atol=1e-12
        )

        print(f"    -> '{law_name}': max |theta_lsim - theta_loop| = {max_diff:.3e}")

    print(
        "[OK] test_lsim_loop_final_consistency (lazo vs lsim único, 4 leyes) superado."
    )


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

    # Caso 2: q literal de la Ec. (13) con min(h) > -1.
    # h in [-0.5, 0.5]: q = (1 - (-0.5)) / (0.5 - (-0.5)) = 1.5.
    # La implementación anterior devolvía 2.0 (max(|q_eq13|, q_span, 1.0)).
    h_centered = np.linspace(-0.5, 0.5, 100)
    q_centered = compute_penalty_factor_q(h_centered, h0_min=-1.0, h0_max=1.0)
    assert np.isclose(
        q_centered, 1.5, atol=1e-9
    ), f"Se esperaba q=1.5 según la Ec. 13, obtenido {q_centered}"

    # h in [0.2, 0.6]: q = (1 - 0.2) / (0.6 - 0.2) = 2.0
    q_low = compute_penalty_factor_q(
        np.linspace(0.2, 0.6, 100), h0_min=-1.0, h0_max=1.0
    )
    assert np.isclose(q_low, 2.0, atol=1e-9)

    # Sobreimpulso (h_max > max(h0)): la fórmula daría q < 1, se aplica el piso q = 1.
    q_overshoot = compute_penalty_factor_q(
        np.linspace(0.6, 1.2, 100), h0_min=-1.0, h0_max=1.0
    )
    assert np.isclose(q_overshoot, 1.0, atol=1e-9)

    # Caso 3: respuesta que alcanza solo el 25% de la excursión: q = 4.0
    h_partial = np.linspace(-1.0, -0.5, 100)
    q_partial = compute_penalty_factor_q(h_partial, h0_min=-1.0, h0_max=1.0)
    assert np.isclose(
        q_partial, 4.0, atol=1e-4
    ), f"Se esperaba q=4.0 (> 1.0), obtenido {q_partial}"

    # Caso 4: Respuesta plana degenerada theta(t) = 0
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

    # H-06: tr0 y ts0 no deben poder sobrescribirse desde la función fitness.
    params = inspect.signature(evaluate_controller_response).parameters
    assert "tr0" not in params and "ts0" not in params
    print("[OK] test_equations_12_and_13 (q literal, OS en % y tr0/ts0 fijos) superado.")


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
    print("[OK] test_chromosome_encoding_and_repair (a < b < c y traslapes) superado.")


def test_skfuzzy_equivalence() -> None:
    """Equivalencia exacta extendida (N-07): automf + cromosomas OPTIMIZADOS.

    Cubre:
    - Controladores baseline generados con `automf`.
    - El cromosoma base (equivalente al controlador lineal PD).
    - Cromosomas aleatorios decodificados/reparados (la forma que produce el GA
      tras la reparación del genotipo).
    - Un cromosoma patológico diseñado para forzar reparación (centros invertidos
      y fuera del universo, anchuras extremas, base de reglas vacía y consecuentes
      fuera de rango), que decodifica a un fenotipo factible.
    Todo el rango de entradas en ambos antecedentes (fracciones uniformes de 0 a 1);
    en los vértices exactos del universo solo se exige finitud y acotación, porque
    scikit-fuzzy recorta la entrada y cae en el caso degenerado de μ==0 en todos
    los términos, mientras que `compute_crisp` define la evaluación saturada sobre
    los nodos interiores (ver docstring de `compute_crisp`).
    """
    rng = np.random.default_rng(2026)

    def build_pathological_chromosome(n_terms, n_genes):
        chrom = rng.uniform(-1.0, 1.0, size=n_genes)
        # Centros invertidos y fuera del universo -> obligan a la reparación
        for off in (0, n_terms):
            idx = np.arange(off, off + n_terms)
            chrom[idx] = np.abs(chrom[idx][::-1])
        chrom[0] = -50.0
        chrom[n_terms - 1] = 50.0
        # Anchuras extremas: por arriba y por debajo del rango permitido [0.20, 1.80]
        chrom[n_terms : 2 * n_terms] = 0.05
        chrom[2 * n_terms : 3 * n_terms] = 2.50
        block = 3 * n_terms
        n_rules = n_terms ** 2
        act_start = 3 * block
        # Base de reglas vacía -> reparación (activa la regla central con penalización)
        chrom[act_start : act_start + n_rules] = 0.0
        # Consecuentes fuera de rango
        chrom[act_start + n_rules : n_genes] = rng.uniform(-2.0, n_terms + 1.0, size=n_rules)
        return chrom

    for n_terms in [5, 7, 9]:
        n_genes = get_num_genes(n_terms)

        chrom_variants = [
            create_baseline_chromosome(n_terms),  # reparación trivial
            build_pathological_chromosome(n_terms, n_genes),  # reparación forzosa
            rng.uniform(-1.0, 1.0, size=n_genes),  # aleatorio reparado
            rng.uniform(-1.0, 1.0, size=n_genes),  # aleatorio reparado
            rng.uniform(-1.0, 1.0, size=n_genes),  # aleatorio reparado
        ]

        # 1) Controlador baseline con automf
        controllers = [
            MamdaniFuzzyController(n_terms=n_terms, use_automf_baseline=True)
        ]
        # 2) Cromosomas optimizados (todos decodificados/reparados por el constructor)
        controllers.extend(
            MamdaniFuzzyController(
                n_terms=n_terms,
                chromosome=chrom,
                use_automf_baseline=False,
                build_control_system_graph=True,
            )
            for chrom in chrom_variants
        )

        # 3) Muestreo del rango completo e x Δe, incluyendo los vértices exactos
        fracs = np.linspace(0.0, 1.0, 11)
        for ctrl_obj in controllers:
            assert ctrl_obj.simulation is not None

            for fe in fracs:
                for fd in fracs:
                    e_val = ERROR_MIN + fe * (ERROR_MAX - ERROR_MIN)
                    de_val = DERROR_MIN + fd * (DERROR_MAX - DERROR_MIN)
                    interior = 0.0 < fe < 1.0 and 0.0 < fd < 1.0

                    v_exact = ctrl_obj.compute_crisp(float(e_val), float(de_val))
                    assert np.isfinite(v_exact)
                    assert VOLTAGE_MIN - 1e-9 <= v_exact <= VOLTAGE_MAX + 1e-9

                    if interior:
                        v_skf = ctrl_obj.compute_with_skfuzzy_sim(
                            float(e_val), float(de_val)
                        )
                        assert np.isclose(
                            v_skf, v_exact, atol=1e-4
                        ), (
                            f"Discrepancia para N={n_terms}, e={e_val:.6f}, "
                            f"de={de_val:.6f}: skfuzzy={v_skf} vs exact={v_exact}"
                        )

    print(
        "[OK] test_skfuzzy_equivalence (automf + optimizados/reparados, "
        "rango completo) superado."
    )


def test_ga_uses_exact_inference() -> None:
    """H-08 / N-06: cada individuo se evalúa con inferencia exacta, sin tablas ni penalización mezclada."""
    assert not hasattr(
        MamdaniFuzzyController, "build_lookup_control_law"
    ), "No debe existir un mecanismo de evaluación simplificada por tabla."

    ga_src = inspect.getsource(ga_optimizer_mod)
    assert "build_lookup_control_law" not in ga_src
    assert "compute_crisp" in ga_src, "El fitness debe evaluar la inferencia exacta."
    assert '"repair_penalty"' in ga_src, "La penalización debe reportarse aparte en el JSON."

    # El cuerpo de fitness_func (hasta la construcción del GA) no debe invocar ni
    # restar repair_penalty: la selección usa exclusivamente la Ec. (12).
    fitness_body = ga_src.split("def fitness_func", 1)[1].split(
        "ga_instance = pygad.GA", 1
    )[0]
    assert "repair_penalty" not in fitness_body, (
        "fitness_func no debe mezclar la penalización de reparación; debe devolver "
        "exclusivamente el fitness exacto de la Ec. (12)."
    )
    print("[OK] test_ga_uses_exact_inference (inferencia exacta y penalización aparte) superado.")


def test_rule_coverage_and_saturation() -> None:
    """H-13 y H-09 (Fase P1): cobertura de la base de reglas y saturación de entradas.

    1. El baseline `automf` con todas las reglas activas cubre TODA la malla
       (e, Δe): ninguna zona muerta (fracción sin regla disparada ≈ 0).
    2. Un controlador con una única regla activa (ZE, ZE) deja la mayor parte de
       la malla sin regla disparada (el GA podría crear zonas muertas al suprimir
       reglas; el JSON de cada controlador final ahora reporta esa fracción).
    3. El diagnóstico de saturación (H-09) cuantifica cuántas muestras del lazo
       se acotan en los bordes de los universos de e y Δe, sin cambiar la
       trayectoria: |e| llega a 2 rad en cada conmutación pero el universo es
       [-π/2, π/2], así que la fracción de saturación de e debe ser > 0.
    """
    # 1) Baseline automf (5): cobertura completa de la malla
    ctrl_base = MamdaniFuzzyController(
        n_terms=5, chromosome=None, use_automf_baseline=True,
        build_control_system_graph=False,
    )
    cov_base = ctrl_base.measure_rule_coverage()
    assert cov_base["covered_fraction"] > 1.0 - 1e-9, (
        f"El baseline automf debería cubrir toda la malla; sin cobertura = "
        f"{cov_base['uncovered_pct']:.3f}%"
    )
    assert cov_base["num_active_rules"] == 25

    # 2) Solo la regla central (ZE, ZE) activa: gran zona muerta
    chrom = create_baseline_chromosome(5)
    act_start = 3 * (3 * 5)          # tras los 3 bloques de funciones de membresía
    n_rules = 25
    chrom[act_start : act_start + n_rules] = 0.0
    mid = act_start + (5 // 2) * 5 + (5 // 2)
    chrom[mid] = 1.0
    ctrl_sparse = MamdaniFuzzyController(
        n_terms=5, chromosome=chrom, use_automf_baseline=False,
        build_control_system_graph=False,
    )
    cov_sparse = ctrl_sparse.measure_rule_coverage()
    assert cov_sparse["num_active_rules"] == 1
    assert cov_sparse["uncovered_fraction"] > 0.6, (
        "Con una sola regla activa debe existir una zona muerta amplia "
        f"(sin cobertura = {cov_sparse['uncovered_pct']:.2f}%)"
    )

    # 3) Diagnóstico de saturación de entradas (H-09)
    simulator = ClosedLoopPlantSimulator()
    # Con ganancia agresiva de error el |e| satura el universo [-π/2, π/2]
    sim_sat = simulator.simulate(lambda e, de: -4.0 * e)
    assert 0.0 <= sim_sat["e_sat_frac"] <= 1.0
    assert 0.0 <= sim_sat["de_sat_frac"] <= 1.0
    assert sim_sat["e_sat_frac"] > 0.0, (
        "El diagnóstico de saturación debe detectar muestras de |e| > π/2 al "
        "conmutar la referencia (+2 rad), y reportarse sin alterar la trayectoria."
    )
    assert sim_sat["lsim_consistency_error"] < 1e-9
    # Con el lazo de salida nula no hay saturación adicional: el contador existe
    sim_zero = simulator.simulate(lambda e, de: 0.0)
    assert "n_sat_e" in sim_zero and "n_sat_de" in sim_zero

    print(
        f"[OK] test_rule_coverage_and_saturation (baseline cov={cov_base['covered_fraction']:.4f}, "
        f"sparse sin cobertura={cov_sparse['uncovered_pct']:.2f}%, e_sat={sim_sat['e_sat_frac']:.3f}) superado."
    )


if __name__ == "__main__":
    test_plant_and_reference()
    test_lsim_loop_final_consistency()
    test_equations_12_and_13()
    test_chromosome_encoding_and_repair()
    test_skfuzzy_equivalence()
    test_ga_uses_exact_inference()
    test_rule_coverage_and_saturation()
    print("=== TODAS LAS PRUEBAS UNITARIAS SUPERADAS EXITOSAMENTE ===")
