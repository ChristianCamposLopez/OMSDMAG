"""Generación de todas las figuras científicas, tablas comparativas y estadísticas.

Cumple con las especificaciones de las Partes 3, 4 y 5 de `Parcial 2.pdf`:
- Tabla Obligatoria de Resultados (pág. 10).
- Estadísticas completas (promedio y desviación estándar de las 5 ejecuciones).
- Gráficas con títulos, ejes, unidades, leyendas y distinción entre corridas individuales,
  promedios y mejores soluciones.
"""

import csv
import json
import os
from typing import Dict, List
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import skfuzzy as fuzz

from src.config import (
    DERROR_MAX,
    DERROR_MIN,
    ERROR_MAX,
    ERROR_MIN,
    LINGUISTIC_LABELS,
    UNIVERSE_RESOLUTION,
    VOLTAGE_MAX,
    VOLTAGE_MIN,
)


def summarize_experiments(
    baselines: Dict[int, Dict[str, object]],
    runs_by_terms: Dict[int, List[Dict[str, object]]],
    tables_dir: str = "results/tables",
) -> Dict[str, object]:
    """Calcula estadísticas (media, desviación estándar, mejor individuo) y exporta tablas."""
    os.makedirs(tables_dir, exist_ok=True)
    summary: Dict[int, Dict[str, object]] = {}

    metric_keys = [
        "fitness",
        "OS_pos",
        "OS_neg",
        "SSE_pos",
        "SSE_neg",
        "tr_pos",
        "tr_neg",
        "ts_pos",
        "ts_neg",
        "q_pos",
        "q_neg",
    ]

    for n_terms, run_list in sorted(runs_by_terms.items()):
        # Seleccionar el mejor individuo exclusivamente según la función fitness (Fase 3)
        best_run = max(run_list, key=lambda r: float(r["metrics"]["fitness"]))

        stats_metrics: Dict[str, Dict[str, float]] = {}
        for k in metric_keys:
            vals = np.array([float(r["metrics"][k]) for r in run_list], dtype=float)
            stats_metrics[k] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
                "best_run_val": float(best_run["metrics"][k]),
            }

        opt_times = np.array([float(r["optimization_time_s"]) for r in run_list])
        inf_times = np.array([float(r["inference_time_ms"]) for r in run_list])
        mem_vals = np.array([float(r["memory_mb"]) for r in run_list])
        act_rules = np.array([float(r["num_active_rules"]) for r in run_list])

        summary[n_terms] = {
            "n_terms": n_terms,
            "num_runs": len(run_list),
            "num_genes": int(best_run["num_genes"]),
            "total_possible_rules": int(best_run["total_possible_rules"]),
            "best_seed": int(best_run["seed"]),
            "best_run": best_run,
            "baseline": baselines[n_terms],
            "metrics_stats": stats_metrics,
            "optimization_time_s": {
                "mean": float(np.mean(opt_times)),
                "std": float(np.std(opt_times, ddof=1)) if len(opt_times) > 1 else 0.0,
                "best": float(best_run["optimization_time_s"]),
            },
            "inference_time_ms": {
                "mean": float(np.mean(inf_times)),
                "std": float(np.std(inf_times, ddof=1)) if len(inf_times) > 1 else 0.0,
                "best": float(best_run["inference_time_ms"]),
            },
            "memory_mb": {
                "mean": float(np.mean(mem_vals)),
                "std": float(np.std(mem_vals, ddof=1)) if len(mem_vals) > 1 else 0.0,
                "best": float(best_run["memory_mb"]),
            },
            "num_active_rules": {
                "mean": float(np.mean(act_rules)),
                "std": float(np.std(act_rules, ddof=1)) if len(act_rules) > 1 else 0.0,
                "best": int(best_run["num_active_rules"]),
            },
        }

    # Guardar resumen estadístico en JSON
    summary_json_path = os.path.join(tables_dir, "statistical_summary.json")
    serializable_summary = {
        str(k): {
            sk: sv
            for sk, sv in v.items()
            if sk not in ("best_run", "baseline")
        }
        for k, v in summary.items()
    }
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(serializable_summary, f, indent=2, ensure_ascii=False)

    # Exportar Tabla Obligatoria de Resultados en Markdown y CSV (Parcial 2.pdf, pág. 10)
    md_lines = _build_mandatory_markdown_table(summary)
    with open(os.path.join(tables_dir, "tabla_obligatoria_resultados.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    _export_all_runs_csv(runs_by_terms, os.path.join(tables_dir, "all_15_runs.csv"))
    return summary


def _build_mandatory_markdown_table(summary: Dict[int, Dict[str, object]]) -> List[str]:
    """Construye la Tabla Obligatoria de Resultados de la página 10 de `Parcial 2.pdf`."""
    s5, s7, s9 = summary[5], summary[7], summary[9]

    def fmt_ms(s: Dict[str, object], key: str, decimals: int = 4) -> str:
        st = s["metrics_stats"][key]
        return f"{st['best_run_val']:.{decimals}f} (media: {st['mean']:.{decimals}f} ± {st['std']:.{decimals}f})"

    lines = [
        "### Tabla Obligatoria de Resultados (`Parcial 2.pdf`, pág. 10)",
        "",
        "| Métrica | 5 términos (Controlador A) | 7 términos (Controlador B) | 9 términos (Controlador C) |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Fitness promedio** (5 corridas) | {s5['metrics_stats']['fitness']['mean']:.4f} ± {s5['metrics_stats']['fitness']['std']:.4f} | {s7['metrics_stats']['fitness']['mean']:.4f} ± {s7['metrics_stats']['fitness']['std']:.4f} | {s9['metrics_stats']['fitness']['mean']:.4f} ± {s9['metrics_stats']['fitness']['std']:.4f} |",
        f"| **Fitness máximo** (mejor corrida) | **{s5['metrics_stats']['fitness']['max']:.4f}** (semilla {s5['best_seed']}) | **{s7['metrics_stats']['fitness']['max']:.4f}** (semilla {s7['best_seed']}) | **{s9['metrics_stats']['fitness']['max']:.4f}** (semilla {s9['best_seed']}) |",
        f"| $OS^+$ (%) | {fmt_ms(s5, 'OS_pos', 4)} | {fmt_ms(s7, 'OS_pos', 4)} | {fmt_ms(s9, 'OS_pos', 4)} |",
        f"| $OS^-$ (%) | {fmt_ms(s5, 'OS_neg', 4)} | {fmt_ms(s7, 'OS_neg', 4)} | {fmt_ms(s9, 'OS_neg', 4)} |",
        f"| $SSE^+$ (rad) | {fmt_ms(s5, 'SSE_pos', 4)} | {fmt_ms(s7, 'SSE_pos', 4)} | {fmt_ms(s9, 'SSE_pos', 4)} |",
        f"| $SSE^-$ (rad) | {fmt_ms(s5, 'SSE_neg', 4)} | {fmt_ms(s7, 'SSE_neg', 4)} | {fmt_ms(s9, 'SSE_neg', 4)} |",
        f"| $t_r^+$ (s) | {fmt_ms(s5, 'tr_pos', 2)} | {fmt_ms(s7, 'tr_pos', 2)} | {fmt_ms(s9, 'tr_pos', 2)} |",
        f"| $t_r^-$ (s) | {fmt_ms(s5, 'tr_neg', 2)} | {fmt_ms(s7, 'tr_neg', 2)} | {fmt_ms(s9, 'tr_neg', 2)} |",
        f"| $t_s^+$ (s) | {fmt_ms(s5, 'ts_pos', 2)} | {fmt_ms(s7, 'ts_pos', 2)} | {fmt_ms(s9, 'ts_pos', 2)} |",
        f"| $t_s^-$ (s) | {fmt_ms(s5, 'ts_neg', 2)} | {fmt_ms(s7, 'ts_neg', 2)} | {fmt_ms(s9, 'ts_neg', 2)} |",
        f"| **Reglas activas** (mejor / media ± DE) | {s5['num_active_rules']['best']} / 25 ({s5['num_active_rules']['mean']:.1f} ± {s5['num_active_rules']['std']:.1f}) | {s7['num_active_rules']['best']} / 49 ({s7['num_active_rules']['mean']:.1f} ± {s7['num_active_rules']['std']:.1f}) | {s9['num_active_rules']['best']} / 81 ({s9['num_active_rules']['mean']:.1f} ± {s9['num_active_rules']['std']:.1f}) |",
        f"| **Número de parámetros optimizados** | {s5['num_genes']} genes | {s7['num_genes']} genes | {s9['num_genes']} genes |",
        f"| **Tiempo de optimización (s)** | {s5['optimization_time_s']['mean']:.2f} ± {s5['optimization_time_s']['std']:.2f} s | {s7['optimization_time_s']['mean']:.2f} ± {s7['optimization_time_s']['std']:.2f} s | {s9['optimization_time_s']['mean']:.2f} ± {s9['optimization_time_s']['std']:.2f} s |",
        f"| **Tiempo promedio de inferencia (ms)** | {s5['inference_time_ms']['mean']:.3f} ± {s5['inference_time_ms']['std']:.3f} ms | {s7['inference_time_ms']['mean']:.3f} ± {s7['inference_time_ms']['std']:.3f} ms | {s9['inference_time_ms']['mean']:.3f} ± {s9['inference_time_ms']['std']:.3f} ms |",
        f"| **Uso de memoria (MB)** | {s5['memory_mb']['mean']:.3f} ± {s5['memory_mb']['std']:.3f} MB | {s7['memory_mb']['mean']:.3f} ± {s7['memory_mb']['std']:.3f} MB | {s9['memory_mb']['mean']:.3f} ± {s9['memory_mb']['std']:.3f} MB |",
    ]
    return lines


def _export_all_runs_csv(
    runs_by_terms: Dict[int, List[Dict[str, object]]], csv_path: str
) -> None:
    """Exporta las 15 ejecuciones independientes a un archivo CSV auditable."""
    fieldnames = [
        "n_terms",
        "seed",
        "fitness",
        "OS_pos",
        "OS_neg",
        "SSE_pos",
        "SSE_neg",
        "tr_pos",
        "tr_neg",
        "ts_pos",
        "ts_neg",
        "q_pos",
        "q_neg",
        "num_active_rules",
        "total_possible_rules",
        "num_genes",
        "optimization_time_s",
        "inference_time_ms",
        "memory_mb",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for n_terms, r_list in sorted(runs_by_terms.items()):
            for r in r_list:
                m = r["metrics"]
                writer.writerow(
                    {
                        "n_terms": n_terms,
                        "seed": r["seed"],
                        "fitness": round(float(m["fitness"]), 6),
                        "OS_pos": round(float(m["OS_pos"]), 6),
                        "OS_neg": round(float(m["OS_neg"]), 6),
                        "SSE_pos": round(float(m["SSE_pos"]), 6),
                        "SSE_neg": round(float(m["SSE_neg"]), 6),
                        "tr_pos": round(float(m["tr_pos"]), 4),
                        "tr_neg": round(float(m["tr_neg"]), 4),
                        "ts_pos": round(float(m["ts_pos"]), 4),
                        "ts_neg": round(float(m["ts_neg"]), 4),
                        "q_pos": round(float(m["q_pos"]), 4),
                        "q_neg": round(float(m["q_neg"]), 4),
                        "num_active_rules": r["num_active_rules"],
                        "total_possible_rules": r["total_possible_rules"],
                        "num_genes": r["num_genes"],
                        "optimization_time_s": round(float(r["optimization_time_s"]), 4),
                        "inference_time_ms": round(float(r["inference_time_ms"]), 4),
                        "memory_mb": round(float(r["memory_mb"]), 4),
                    }
                )


def generate_all_figures(
    baselines: Dict[int, Dict[str, object]],
    runs_by_terms: Dict[int, List[Dict[str, object]]],
    summary: Dict[int, Dict[str, object]],
    figures_dir: str = "results/figures",
) -> List[str]:
    """Genera el conjunto completo de gráficas obligatorias en alta resolución."""
    os.makedirs(figures_dir, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "figure.dpi": 150,
            "axes.grid": True,
            "grid.alpha": 0.3,
        }
    )
    saved_files: List[str] = []

    colors = {5: "#1f77b4", 7: "#ff7f0e", 9: "#2ca02c"}

    # -------------------------------------------------------------------------
    # FIGURA 1: Respuesta temporal de los Controladores Base (automf sin GA)
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    t_vec = np.array(baselines[5]["trajectory"]["t"])
    r_vec = np.array(baselines[5]["trajectory"]["r"])
    axes[0].plot(t_vec, r_vec, "k--", lw=1.8, label="Referencia cuadrada r(t) [±1 rad]")
    for n in [5, 7, 9]:
        th = np.array(baselines[n]["trajectory"]["theta"])
        u_v = np.array(baselines[n]["trajectory"]["u"])
        fit_b = baselines[n]["metrics"]["fitness"]
        axes[0].plot(
            t_vec,
            th,
            color=colors[n],
            lw=1.5,
            label=f"Baseline {n} términos (automf) — Fitness={fit_b:.4f}",
        )
        axes[1].plot(
            t_vec,
            u_v,
            color=colors[n],
            lw=1.3,
            label=f"Voltaje v(t) Baseline {n} términos",
        )
    axes[0].axvspan(0, 50, color="gray", alpha=0.12, label="Transición inicial 0→1 (descartada)")
    axes[0].set_ylabel("Posición angular θ(t) [rad]")
    axes[0].set_title("Fase 1: Respuesta Temporal de los Controladores Base (automf, sin optimización genética)")
    axes[0].legend(loc="lower right", fontsize=8.5)
    axes[1].set_ylabel("Voltaje de control v(t) [V]")
    axes[1].set_xlabel("Tiempo t [s]")
    axes[1].set_ylim(-8.6, 8.6)
    axes[1].legend(loc="lower right", fontsize=8.5)
    fig.tight_layout()
    f1_path = os.path.join(figures_dir, "fig1_baselines_response.png")
    fig.savefig(f1_path, bbox_inches="tight")
    plt.close(fig)
    saved_files.append(f1_path)

    # -------------------------------------------------------------------------
    # FIGURA 2: Comparación de Respuesta Temporal de los Mejores Optimizados (5, 7 y 9)
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(3, 1, figsize=(12, 9.5))
    axes[0].plot(t_vec, r_vec, "k--", lw=1.8, label="Referencia cuadrada r(t) [±1 rad]")
    for n in [5, 7, 9]:
        best_r = summary[n]["best_run"]
        th = np.array(best_r["trajectory"]["theta"])
        u_v = np.array(best_r["trajectory"]["u"])
        fit_v = best_r["metrics"]["fitness"]
        axes[0].plot(
            t_vec,
            th,
            color=colors[n],
            lw=1.6,
            label=f"Mejor {n} términos (semilla {best_r['seed']}) — Fitness={fit_v:.4f}",
        )
        axes[2].plot(
            t_vec,
            u_v,
            color=colors[n],
            lw=1.2,
            alpha=0.85,
            label=f"Voltaje v(t) — {n} términos ({best_r['num_active_rules']}/{best_r['total_possible_rules']} reglas)",
        )

    axes[0].axvspan(0, 50, color="gray", alpha=0.12, label="0–50 s descartado (0→+1)")
    axes[0].set_ylabel("Posición θ(t) [rad]")
    axes[0].set_title("Respuesta Temporal en Lazo Cerrado (scipy.signal.lsim, T_sim = 200 s) — Mejores Individuos")
    axes[0].legend(loc="lower right", fontsize=8.5)

    # Zoom en la transición positiva [100, 150] s con bandas del 10%, 90% y ±5%
    mask_zoom = (t_vec >= 98.0) & (t_vec <= 145.0)
    axes[1].plot(t_vec[mask_zoom], r_vec[mask_zoom], "k--", lw=1.6, label="Referencia (-1 → +1 rad)")
    axes[1].axhline(0.95, color="gray", ls=":", lw=1.0, label="Banda de establecimiento ±5% ([0.95, 1.05] rad)")
    axes[1].axhline(1.05, color="gray", ls=":", lw=1.0)
    axes[1].axhline(-0.80, color="purple", ls="-.", lw=0.8, alpha=0.6, label="Umbrales 10% (-0.8 rad) y 90% (+0.8 rad)")
    axes[1].axhline(0.80, color="purple", ls="-.", lw=0.8, alpha=0.6)
    for n in [5, 7, 9]:
        best_r = summary[n]["best_run"]
        th = np.array(best_r["trajectory"]["theta"])
        m = best_r["metrics"]
        axes[1].plot(
            t_vec[mask_zoom],
            th[mask_zoom],
            color=colors[n],
            lw=1.7,
            label=f"{n} térm.: tr+={m['tr_pos']:.2f}s, ts+={m['ts_pos']:.2f}s, OS+={m['OS_pos']:.4f}%",
        )
    axes[1].set_ylabel("Posición θ(t) [rad]")
    axes[1].set_title("Detalle de la Transición Positiva (-1 → +1 rad en t ∈ [100, 150) s)")
    axes[1].legend(loc="lower right", fontsize=8.5)

    axes[2].set_ylabel("Voltaje v(t) [V]")
    axes[2].set_xlabel("Tiempo t [s]")
    axes[2].set_ylim(-8.6, 8.6)
    axes[2].set_title("Señal de Control Generada por el Controlador Difuso v(t) ∈ [-8.18, 8.18] V")
    axes[2].legend(loc="lower right", fontsize=8.5)
    fig.tight_layout()
    f2_path = os.path.join(figures_dir, "fig2_optimized_temporal_comparison.png")
    fig.savefig(f2_path, bbox_inches="tight")
    plt.close(fig)
    saved_files.append(f2_path)

    # -------------------------------------------------------------------------
    # FIGURA 3: Curvas de Convergencia (Generación vs Fitness) de las 5 Semillas
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for idx, n in enumerate([5, 7, 9]):
        ax = axes[idx]
        histories = []
        for r in runs_by_terms[n]:
            h = np.array(r["fitness_history"], dtype=float)
            histories.append(h)
            gens = np.arange(len(h))
            ax.plot(
                gens,
                h,
                color=colors[n],
                alpha=0.30,
                lw=1.1,
                label=f"Semilla {r['seed']}" if idx == 0 else None,
            )
        hist_mat = np.vstack(histories)
        mean_h = np.mean(hist_mat, axis=0)
        std_h = np.std(hist_mat, axis=0, ddof=1)
        best_h = np.array(summary[n]["best_run"]["fitness_history"], dtype=float)
        gens = np.arange(len(mean_h))

        ax.plot(gens, mean_h, color=colors[n], lw=2.4, label="Promedio (5 corridas)")
        ax.plot(gens, best_h, "k--", lw=1.6, label=f"Mejor corrida (semilla {summary[n]['best_seed']})")
        ax.fill_between(
            gens,
            mean_h - std_h,
            mean_h + std_h,
            color=colors[n],
            alpha=0.18,
            label="±1 Desv. Estándar",
        )
        ax.axhline(
            baselines[n]["metrics"]["fitness"],
            color="red",
            ls=":",
            lw=1.3,
            label=f"Baseline automf ({baselines[n]['metrics']['fitness']:.3f})",
        )
        ax.set_title(f"Controlador de {n} términos ({summary[n]['num_genes']} genes)")
        ax.set_xlabel("Generación")
        if idx == 0:
            ax.set_ylabel("Fitness (Ecuación 12)")
        ax.legend(loc="lower right", fontsize=8)
    fig.suptitle(
        "Evolución de la Aptitud Durante la Optimización con PyGAD (5 Ejecuciones Independientes por Configuración)",
        y=1.02,
        fontsize=12,
    )
    fig.tight_layout()
    f3_path = os.path.join(figures_dir, "fig3_convergence_curves.png")
    fig.savefig(f3_path, bbox_inches="tight")
    plt.close(fig)
    saved_files.append(f3_path)

    # -------------------------------------------------------------------------
    # FIGURAS 4, 5 y 6: Funciones de Membresía Antes (automf) y Después (PyGAD)
    # -------------------------------------------------------------------------
    for idx_fig, n in enumerate([5, 7, 9], start=4):
        f_mf = _plot_mfs_before_after(
            n_terms=n,
            baseline_rec=baselines[n],
            best_rec=summary[n]["best_run"],
            out_path=os.path.join(figures_dir, f"fig{idx_fig}_mfs_before_after_{n}terms.png"),
        )
        saved_files.append(f_mf)

    # -------------------------------------------------------------------------
    # FIGURA 7: Mapas de Reglas Activas e Inactivas y Consecuentes (5, 7 y 9)
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2))
    for idx, n in enumerate([5, 7, 9]):
        ax = axes[idx]
        best_r = summary[n]["best_run"]
        act = np.array(best_r["decoded_mfs"]["rule_active"], dtype=int)
        cons = np.array(best_r["decoded_mfs"]["rule_consequent"], dtype=int)
        labels = LINGUISTIC_LABELS[n]

        # Matriz visual: -1 si inactiva, 0..N-1 si activa
        vis_mat = np.where(act == 1, cons, -1)
        cmap = plt.cm.get_cmap("YlGnBu", n)
        masked = np.ma.masked_where(vis_mat < 0, vis_mat)
        ax.set_facecolor("#f0f0f0")
        im = ax.imshow(masked, cmap=cmap, vmin=0, vmax=n - 1)

        for i in range(n):
            for j in range(n):
                if act[i, j] == 1:
                    lbl = labels[cons[i, j]]
                    txt_color = "white" if cons[i, j] > n * 0.6 else "black"
                    ax.text(j, i, lbl, ha="center", va="center", color=txt_color, fontsize=8, fontweight="bold")
                else:
                    ax.text(j, i, "OFF", ha="center", va="center", color="#999999", fontsize=7)

        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Cambio del error Δe(t)")
        ax.set_ylabel("Error e(t)")
        ax.set_title(
            f"{n} términos: {best_r['num_active_rules']}/{best_r['total_possible_rules']} reglas activas "
            f"({100.0*best_r['num_active_rules']/best_r['total_possible_rules']:.1f}%)"
        )
        ax.grid(False)
    fig.suptitle(
        "Base de Reglas Difusas Optimizadas (Celdas Activas con su Consecuente de Voltaje vs Reglas Desactivadas 'OFF')",
        y=1.02,
        fontsize=12,
    )
    fig.tight_layout()
    f7_path = os.path.join(figures_dir, "fig7_active_rules_heatmaps.png")
    fig.savefig(f7_path, bbox_inches="tight")
    plt.close(fig)
    saved_files.append(f7_path)

    # -------------------------------------------------------------------------
    # FIGURA 8: Comparación Estadística de Métricas y Costos Computacionales
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    x_pos = np.arange(3)
    x_labels = ["5 términos\n(95 genes)", "7 términos\n(161 genes)", "9 términos\n(243 genes)"]
    bar_colors = [colors[5], colors[7], colors[9]]

    # 8a: Fitness promedio ± DE vs Baseline
    means_fit = [summary[n]["metrics_stats"]["fitness"]["mean"] for n in [5, 7, 9]]
    stds_fit = [summary[n]["metrics_stats"]["fitness"]["std"] for n in [5, 7, 9]]
    maxs_fit = [summary[n]["metrics_stats"]["fitness"]["max"] for n in [5, 7, 9]]
    base_fit = [baselines[n]["metrics"]["fitness"] for n in [5, 7, 9]]
    width = 0.28
    axes[0, 0].bar(x_pos - width, base_fit, width, label="Baseline (automf)", color="#888888")
    axes[0, 0].bar(x_pos, means_fit, width, yerr=stds_fit, capsize=5, label="Media ± DE (5 corridas)", color=bar_colors)
    axes[0, 0].bar(x_pos + width, maxs_fit, width, label="Máximo (Mejor corrida)", color="#222222", alpha=0.8)
    axes[0, 0].set_xticks(x_pos)
    axes[0, 0].set_xticklabels(x_labels)
    axes[0, 0].set_ylabel("Fitness (Ec. 12)")
    axes[0, 0].set_title("Fitness: Baseline vs Optimizado (5 corridas)")
    axes[0, 0].legend(fontsize=8)

    # 8b: Tiempos de subida tr+ y tr- y establecimiento ts+ y ts-
    tr_p = [summary[n]["metrics_stats"]["tr_pos"]["mean"] for n in [5, 7, 9]]
    tr_p_sd = [summary[n]["metrics_stats"]["tr_pos"]["std"] for n in [5, 7, 9]]
    ts_p = [summary[n]["metrics_stats"]["ts_pos"]["mean"] for n in [5, 7, 9]]
    ts_p_sd = [summary[n]["metrics_stats"]["ts_pos"]["std"] for n in [5, 7, 9]]
    axes[0, 1].bar(x_pos - 0.18, tr_p, 0.34, yerr=tr_p_sd, capsize=4, label="tr+ (Media ± DE)", color="#1f77b4")
    axes[0, 1].bar(x_pos + 0.18, ts_p, 0.34, yerr=ts_p_sd, capsize=4, label="ts+ (Media ± DE)", color="#ff7f0e")
    axes[0, 1].axhline(9.0, color="#1f77b4", ls="--", lw=1.0, label="tr0 = 9 s")
    axes[0, 1].axhline(13.0, color="#ff7f0e", ls="--", lw=1.0, label="ts0 = 13 s")
    axes[0, 1].set_xticks(x_pos)
    axes[0, 1].set_xticklabels(x_labels)
    axes[0, 1].set_ylabel("Tiempo [s]")
    axes[0, 1].set_title("Tiempos Transitorios tr+ y ts+ (5 corridas)")
    axes[0, 1].legend(fontsize=8)

    # 8c: SSE+ y OS+
    sse_p = [summary[n]["metrics_stats"]["SSE_pos"]["mean"] for n in [5, 7, 9]]
    sse_sd = [summary[n]["metrics_stats"]["SSE_pos"]["std"] for n in [5, 7, 9]]
    os_p = [summary[n]["metrics_stats"]["OS_pos"]["mean"] for n in [5, 7, 9]]
    os_sd = [summary[n]["metrics_stats"]["OS_pos"]["std"] for n in [5, 7, 9]]
    axes[0, 2].bar(x_pos - 0.18, sse_p, 0.34, yerr=sse_sd, capsize=4, label="SSE+ [rad]", color="#2ca02c")
    axes[0, 2].bar(x_pos + 0.18, os_p, 0.34, yerr=os_sd, capsize=4, label="OS+ [%]", color="#d62728")
    axes[0, 2].set_xticks(x_pos)
    axes[0, 2].set_xticklabels(x_labels)
    axes[0, 2].set_ylabel("Magnitud (SSE [rad] / OS [%])")
    axes[0, 2].set_title("Error en Estado Estable (SSE+) y Overshoot (OS+ [%])")
    axes[0, 2].legend(fontsize=8)

    # 8d: Tiempo total de optimización (s)
    opt_m = [summary[n]["optimization_time_s"]["mean"] for n in [5, 7, 9]]
    opt_sd = [summary[n]["optimization_time_s"]["std"] for n in [5, 7, 9]]
    axes[1, 0].bar(x_pos, opt_m, 0.45, yerr=opt_sd, capsize=5, color=bar_colors)
    axes[1, 0].set_xticks(x_pos)
    axes[1, 0].set_xticklabels(x_labels)
    axes[1, 0].set_ylabel("Tiempo de optimización [s]")
    axes[1, 0].set_title("Costo de Optimización (Media ± DE de 5 corridas)")

    # 8e: Tiempo promedio de inferencia (ms)
    inf_m = [summary[n]["inference_time_ms"]["mean"] for n in [5, 7, 9]]
    inf_sd = [summary[n]["inference_time_ms"]["std"] for n in [5, 7, 9]]
    axes[1, 1].bar(x_pos, inf_m, 0.45, yerr=inf_sd, capsize=5, color=bar_colors)
    axes[1, 1].set_xticks(x_pos)
    axes[1, 1].set_xticklabels(x_labels)
    axes[1, 1].set_ylabel("Tiempo de inferencia [ms]")
    axes[1, 1].set_title("Costo de Inferencia por Muestra (controller.compute)")

    # 8f: Reglas activas vs Reglas totales posibles
    tot_r = [summary[n]["total_possible_rules"] for n in [5, 7, 9]]
    act_m = [summary[n]["num_active_rules"]["mean"] for n in [5, 7, 9]]
    act_sd = [summary[n]["num_active_rules"]["std"] for n in [5, 7, 9]]
    axes[1, 2].bar(x_pos - 0.18, tot_r, 0.34, label="Reglas totales (N²)", color="#cccccc")
    axes[1, 2].bar(x_pos + 0.18, act_m, 0.34, yerr=act_sd, capsize=5, label="Reglas activas (Media ± DE)", color=bar_colors)
    axes[1, 2].set_xticks(x_pos)
    axes[1, 2].set_xticklabels(x_labels)
    axes[1, 2].set_ylabel("Número de reglas")
    axes[1, 2].set_title("Poda Evolutiva de Reglas Activas vs Base Completa")
    axes[1, 2].legend(fontsize=8)

    fig.suptitle(
        "Comparación Estadística de Desempeño y Costo Computacional (Promedio ± Desviación Estándar, 5 Semillas)",
        y=1.02,
        fontsize=12,
    )
    fig.tight_layout()
    f8_path = os.path.join(figures_dir, "fig8_metrics_and_computational_cost.png")
    fig.savefig(f8_path, bbox_inches="tight")
    plt.close(fig)
    saved_files.append(f8_path)

    return saved_files


def _plot_mfs_before_after(
    n_terms: int,
    baseline_rec: Dict[str, object],
    best_rec: Dict[str, object],
    out_path: str,
) -> str:
    """Grafica las funciones de pertenencia antes (automf) y después (optimizado) para e, de, v."""
    labels = LINGUISTIC_LABELS[n_terms]
    fig, axes = plt.subplots(3, 2, figsize=(13, 8.5), sharey=True)

    vars_spec = [
        ("Error e(t) [rad]", "error_mfs", np.linspace(ERROR_MIN, ERROR_MAX, UNIVERSE_RESOLUTION)),
        ("Cambio del error Δe(t) [rad/s]", "derror_mfs", np.linspace(DERROR_MIN, DERROR_MAX, UNIVERSE_RESOLUTION)),
        ("Voltaje v(t) [V]", "voltage_mfs", np.linspace(VOLTAGE_MIN, VOLTAGE_MAX, UNIVERSE_RESOLUTION)),
    ]

    cmap = plt.cm.get_cmap("tab10", n_terms)
    for row_idx, (var_title, mf_key, univ) in enumerate(vars_spec):
        base_mfs = np.array(baseline_rec["decoded_mfs"][mf_key], dtype=float)
        opt_mfs = np.array(best_rec["decoded_mfs"][mf_key], dtype=float)

        ax_before = axes[row_idx, 0]
        ax_after = axes[row_idx, 1]

        for k in range(n_terms):
            mu_b = fuzz.trimf(univ, base_mfs[k])
            mu_o = fuzz.trimf(univ, opt_mfs[k])
            ax_before.plot(univ, mu_b, lw=1.6, color=cmap(k), label=labels[k])
            ax_after.plot(univ, mu_o, lw=1.6, color=cmap(k), label=labels[k])
            ax_after.fill_between(univ, 0, mu_o, color=cmap(k), alpha=0.10)

        ax_before.set_title(f"Antes (automf): {var_title}")
        ax_after.set_title(f"Después (Optimizado PyGAD, semilla {best_rec['seed']}): {var_title}")
        ax_before.set_ylabel("Grado μ")
        ax_before.set_xlim(univ[0], univ[-1])
        ax_after.set_xlim(univ[0], univ[-1])
        if row_idx == 0:
            ax_after.legend(loc="upper right", fontsize=8, ncol=min(n_terms, 5))

    fig.suptitle(
        f"Funciones de Membresía Antes y Después de la Optimización — Controlador de {n_terms} Términos",
        y=1.02,
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path

