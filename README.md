# Optimización Multiobjetivo de Sistemas Difusos Mamdani mediante Algoritmos Genéticos (OMSDMAG)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PyGAD](https://img.shields.io/badge/PyGAD-3.3%2B-orange)
![SciPy](https://img.shields.io/badge/SciPy-lsim-green?logo=scipy)
![scikit-fuzzy](https://img.shields.io/badge/scikit--fuzzy-0.4.2-red)
![License](https://img.shields.io/badge/License-Academic-lightgrey)

Proyecto de investigación y desarrollo enfocado en el diseño y optimización evolutiva paramétrica/estructural de controladores difusos tipo Mamdani para el control en lazo cerrado de la posición angular de un servomotor de corriente directa (CD). Desarrollado conforme a las especificaciones rigurosas de `Parcial 2.pdf` y basado en la metodología científica de **Téllez-Velázquez et al. (2017)** (*Int. J. Fuzzy Syst.*, DOI: [10.1007/s40815-017-0307-0](https://doi.org/10.1007/s40815-017-0307-0)).

---

## 📋 Descripción del Proyecto

El proyecto implementa una arquitectura modular, reproducible y reproducible en Python para:

1. **Simulación Dinámica de la Planta:** Modelar dinómicamente con `scipy.signal.lsim` la planta continua del servomotor de CD de 3.er orden:
   $$G(s) = \frac{0.5}{s^3 + 13.6667s^2 + 23.3487s}$$
   Evaluada durante un horizonte temporal estricto de $T_{\text{sim}} = 200\text{ s}$ con condiciones iniciales nulas $\mathbf{x}_0 = [0, 0, 0]^T$, en ausencia de ruido y ante una señal de referencia cuadrada de amplitud $\pm 1\text{ rad}$ (período de $100\text{ s}$, ciclo de trabajo del 50%).

2. **Controladores Difusos Mamdani:** Implementados con `scikit-fuzzy` para configuraciones de **5, 7 y 9 términos lingüísticos** por entrada ($e$, $\Delta e$) y salida ($v$), respetando los universos de discurso fijos:
   - **Error de posición ($e$):** $\mathcal{U}_e = \left[-\frac{\pi}{2}, \frac{\pi}{2}\right]\text{ rad}$
   - **Cambio del error ($\Delta e$):** $\mathcal{U}_{\Delta e} = \left[-\frac{\pi}{6}, \frac{\pi}{6}\right]\text{ rad/s}$
   - **Voltaje de control ($v$):** $\mathcal{U}_v = [-8.18, 8.18]\text{ V}$

3. **Optimización Evolutiva Coadaptativa (`pygad`):** Configurado con `sol_per_pop = 20` y `num_generations = 30` a lo largo de 5 ejecuciones independientes con semillas aleatorias distintas (`[42, 100, 2026, 777, 999]`):
   - Geometría de funciones de membresía triangulares (`skfuzzy.trimf`), asegurando el ordenamiento estricto de vértices $a_k < b_k < c_k$.
   - Activación/desactivación de reglas difusas (poda binaria $1/0$).
   - Consecuentes lingüísticos de la matriz de inferencia.

4. **Función de Aptitud Multiobjetivo Transitoria (MOTFF):** Evaluación explícita sobre 8 métricas dinámicas (descartando la transición inicial $[0, 50)\text{ s}$):
   - **Transición Positiva ($-1 \to +1\text{ rad}$):** $OS^+$, $SSE^+$, $t_r^+$, $t_s^+$.
   - **Transición Negativa ($+1 \to -1\text{ rad}$):** $OS^-$, $SSE^-$, $t_r^-$, $t_s^-$.
   - **Parámetros de diseño:** Metas $t_r^0 = 9\text{ s}$, $t_s^0 = 13\text{ s}$, pesos equitativos $w_1 = \dots = w_8 = 0.125$ y el factor de penalización del tiempo de crecimiento $q \ge 1.0$ (Ec. 13 del artículo):
     $$q = \max\left(1.0, \frac{\max(h_0) - \min(h_i)}{\max(h) - \min(h)}\right)$$

---

## 🗂️ Estructura del Repositorio

```text
.
├── Parcial 2.pdf                                 # Documento rector de la actividad
├── IJFS-D-16-00634_R1.pdf                        # Artículo científico de referencia
├── Parcial2_ComputacionFlexible.ipynb            # Libreta Jupyter ejecutable (Run All) con reporte y 30 preguntas
├── Reporte_Parcial2_ComputacionFlexible.docx     # Reporte técnico completo en formato Word
├── main.py                                       # Script principal para reproducir todos los experimentos
├── build_deliverables.py                         # Generador automatizado del Notebook y el reporte DOCX
├── docs/                                         # Documentación de seguimiento
│   └── AUDITORIA_PARCIAL2.md                     # Hallazgos de la auditoría y plan de correcciones
├── src/                                          # Código fuente modular
│   ├── config.py                                 # Parámetros, constantes y universos de discurso
│   ├── plant_sim.py                              # Planta LTI y simulación estricta con scipy.signal.lsim
│   ├── fuzzy_controller.py                       # Controlador Mamdani (skfuzzy) y medición de tiempos/memoria
│   ├── chromosome.py                             # Codificación, decodificación y reparación (a < b < c)
│   ├── metrics_fitness.py                        # Métricas transitorias, OS en %, Ec. (12) y Ec. (13)
│   ├── ga_optimizer.py                           # Optimización evolutiva con PyGAD (5 semillas)
│   └── plotting_tables.py                        # Generación de gráficas científicas y tablas
├── tests/                                        # Suite de pruebas unitarias de verificación
│   └── test_verification.py                      # Verificación de lsim, Ec. 12/13, OS (%) y orden a < b < c
└── results/                                      # Resultados experimentales auditables
    ├── baselines/                                # Evaluaciones de los 3 controladores base (automf)
    ├── runs/                                     # 15 corridas genéticas independientes (JSON)
    ├── figures/                                  # 8 figuras científicas en alta resolución
    └── tables/                                   # Tablas estadísticas en Markdown, CSV y JSON

```

---

## 🚀 Ejecución y Pruebas

Este proyecto utiliza `uv` para la gestión rápida de entornos virtuales y dependencias.

### 1. Pruebas Unitarias de Verificación

Para validar la consistencia matemática de `lsim`, las Ecuaciones (12) e (13) y la reparación de cromosomas:

```bash
uv run python -m tests.test_verification

```

### 2. Campaña Experimental Completa (3 Baselines + 15 Corridas PyGAD)

Para cargar los resultados existentes de la memoria caché y regenerar tablas/figuras:

```bash
uv run python main.py

```

Para forzar la re-ejecución evolutiva completa desde cero (procesamiento en paralelo):

```bash
uv run python main.py --force

```

### 3. Generación Automatizada de Entregables

Para reconstruir el Notebook `.ipynb` interactivo y el documento en Word `.docx`:

```bash
uv run python build_deliverables.py

```

---

## 📊 Resumen de Resultados Experimentales

La siguiente tabla resume los hallazgos cuantitativos promediados sobre 5 ejecuciones independientes por configuración (valores expresados como $\text{Mejor} \text{ (Media} \pm \text{DE)}$):

| Métrica | 5 Términos (Controlador A) | 7 Términos (Controlador B) | 9 Términos (Controlador C) |
| --- | --- | --- | --- |
| **Fitness promedio** (5 corridas) | $0.7218 \pm 0.0488$ | $0.7299 \pm 0.0593$ | $0.7134 \pm 0.0649$ |
| **Fitness máximo** (mejor corrida) | **0.7616** (semilla 999) | **0.8199** (semilla 42) | **0.7946** (semilla 999) |
| $OS^+$ (%) | 0.0577 (media: $0.0115 \pm 0.0258$) | 0.7896 (media: $1.2004 \pm 1.3434$) | 0.0000 (media: $0.4326 \pm 0.9673$) |
| $OS^-$ (%) | 0.0000 (media: $0.2439 \pm 0.5453$) | 0.0000 (media: $0.0000 \pm 0.0000$) | 1.3638 (media: $1.2498 \pm 1.9562$) |
| $SSE^+$ (rad) | 0.0031 (media: $0.0390 \pm 0.0508$) | 0.0063 (media: $0.0213 \pm 0.0089$) | 0.0144 (media: $0.0879 \pm 0.1139$) |
| $SSE^-$ (rad) | 0.0104 (media: $0.0344 \pm 0.0235$) | 0.0060 (media: $0.0379 \pm 0.0303$) | 0.0122 (media: $0.0478 \pm 0.0649$) |
| $t_r^+$ (s) | 11.70 (media: $15.90 \pm 5.82$) | 13.40 (media: $17.50 \pm 5.85$) | 14.70 (media: $21.80 \pm 16.08$) |
| $t_r^-$ (s) | 30.40 (media: $21.80 \pm 9.01$) | 11.70 (media: $14.90 \pm 3.99$) | 11.30 (media: $18.99 \pm 10.64$) |
| $t_s^+$ (s) | 16.80 (media: $27.50 \pm 15.23$) | 17.60 (media: $27.38 \pm 10.96$) | 18.60 (media: $30.60 \pm 17.79$) |
| $t_s^-$ (s) | 40.40 (media: $42.26 \pm 10.17$) | 15.60 (media: $30.45 \pm 16.94$) | 15.10 (media: $24.36 \pm 14.90$) |
| **Reglas activas** (mejor / media $\pm$ DE) | 16 / 25 ($17.4 \pm 3.4$) | 39 / 49 ($35.8 \pm 4.1$) | 58 / 81 ($54.4 \pm 7.8$) |
| **Parámetros optimizados** | **95 genes** | **161 genes** | **243 genes** |
| **Tiempo de optimización (s)** | $169.63 \pm 1.47\text{ s}$ | $172.32 \pm 0.76\text{ s}$ | $181.87 \pm 0.81\text{ s}$ |
| **Tiempo de inferencia (ms)** | $10.065 \pm 0.762\text{ ms}$ | $22.761 \pm 2.088\text{ ms}$ | $36.585 \pm 5.642\text{ ms}$ |
| **Uso de memoria (MB)** | $0.491 \pm 0.037\text{ MB}$ | $0.884 \pm 0.071\text{ MB}$ | $1.436 \pm 0.205\text{ MB}$ |

---

## ⚡ Verificación Opcional de Aceleración por Hardware (GPU)

Aunque el algoritmo evolutivo se ejecuta completamente en CPU conforme a las especificaciones del parcial, puedes verificar que tu entorno reconozca hardware de aceleración (ej. NVIDIA RTX 5060) mediante `uv`:

```bash
uv run python - <<'PY'
import torch
print('CUDA disponible:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU detectada:', torch.cuda.get_device_name(0))
PY

```

En caso de requerir sincronizar el grupo CUDA:

```bash
uv sync --group cuda

```

***

### Cambios principales aplicados:
1. **Corrección de ecuaciones matemáticas:** Toda la función de transferencia $G(s)$, los universos de discurso y el factor de penalización $q$ se integraron en bloques $\text{\LaTeX}$ limpios de una sola línea (`$$...$$` y `$..$`).
2. **Formateo de la Tabla de Resultados:** Se reconstruyó el código Markdown para generar una tabla alineada con separadores claros (`| :--- | :---: | ... |`).
3. **Comandos con `uv`:** Se estandarizaron todas las órdenes del sistema (`python main.py`, etc.) prefijadas con `uv run` para mantener la coherencia con tu flujo de desarrollo.
4. **Presentación visual:** Se añadieron escudos (*badges*) superiores con las bibliotecas principales del proyecto.
