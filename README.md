# Optimización Multiobjetivo de Sistemas Difusos Mamdani mediante Algoritmos Genéticos (OMSDMAG)

Proyecto de investigación y desarrollo para el diseño y optimización evolutiva de controladores difusos tipo Mamdani aplicados al control en lazo cerrado de la posición angular de un servomotor de corriente directa (CD). Desarrollado conforme a las especificaciones de **`Parcial 2.pdf`** y la metodología del artículo científico de referencia **Téllez-Velázquez et al. (2017)** (*`IJFS-D-16-00634_R1.pdf`*, DOI: `10.1007/s40815-017-0307-0`).

---

## 📋 Descripción del Proyecto

El proyecto implementa una arquitectura modular, reproducible y verificable en Python para:
1. **Modelar y simular estrictamente con `scipy.signal.lsim`** la dinámica continua del servomotor de CD de tercer orden:
   $$G(s) = \frac{0.5}{s^3 + 13.6667 s^2 + 23.3487 s}$$
   durante un horizonte de $T_{\text{sim}} = 200\text{ s}$ con condiciones iniciales nulas `x0 = [0, 0, 0]`, en ausencia total de ruido y ante una señal de referencia cuadrada de amplitud $\pm 1\text{ rad}$ y período de $100\text{ s}$.
2. **Implementar controladores difusos Mamdani (`scikit-fuzzy`)** con **5, 7 y 9 términos lingüísticos** por variable de entrada (`error`, `derror`) y de salida (`voltage`), respetando los universos de discurso fijos:
   - Error: $e \in [-\pi/2, \pi/2]\text{ rad}$
   - Cambio del error: $\Delta e \in [-\pi/6, \pi/6]\text{ rad/s}$
   - Voltaje de control: $v \in [-8.18, 8.18]\text{ V}$
3. **Optimizar simultáneamente con `pygad`** (`sol_per_pop = 20`, `num_generations = 30`, 5 semillas independientes por configuración):
   - La forma, centros y traslapes de las funciones de membresía triangulares (`skfuzzy.trimf`) de entradas y salida, garantizando siempre el **orden estricto $a < b < c$**.
   - La activación y desactivación de reglas difusas ($1/0$).
   - Los consecuentes lingüísticos de cada regla.
4. **Evaluar la Función Fitness Multiobjetivo Transitoria (Ecuaciones 12 y 13 del artículo)** sobre las 8 métricas obligatorias (descartando la transición inicial $0 \to +1\text{ rad}$ de los primeros $50\text{ s}$):
   - Transición positiva ($-1 \to +1\text{ rad}$): $OS^+$ (`%`), $SSE^+$ (`rad`), $t_r^+$ (`s`), $t_s^+$ (`s`).
   - Transición negativa ($+1 \to -1\text{ rad}$): $OS^-$ (`%`), $SSE^-$ (`rad`), $t_r^-$ (`s`), $t_s^-$ (`s`).
   - Con $t_r^0 = 9\text{ s}$, $t_s^0 = 13\text{ s}$, pesos $w_1 = \dots = w_8 = 0.125$ y factor de penalización del tiempo de crecimiento $q = \frac{\max(h^0)-\min(h_i)}{\max(h)-\min(h)} \ge 1.0$ (Ecuación 13).

---

## 🗂️ Estructura del Repositorio

```text
├── Parcial 2.pdf                                 # Documento rector de la actividad
├── IJFS-D-16-00634_R1.pdf                        # Artículo científico de referencia
├── Parcial2_ComputacionFlexible.ipynb            # Libreta Jupyter ejecutable (Run All) con reporte y 30 preguntas
├── Reporte_Parcial2_ComputacionFlexible.docx     # Reporte técnico completo en formato Word
├── main.py                                       # Script principal para reproducir todos los experimentos
├── build_deliverables.py                         # Generador automatizado del Notebook y el reporte DOCX
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

### 1. Ejecutar las pruebas unitarias de verificación
```bash
python -m tests.test_verification
```

### 2. Ejecutar la campaña experimental completa (3 baselines + 15 corridas PyGAD)
```bash
# Cargar resultados existentes y regenerar tablas/figuras
python main.py

# Forzar la re-ejecución completa desde cero de las 15 corridas en paralelo
python main.py --force
```

### 3. Regenerar la Libreta Jupyter y el Reporte Word
```bash
python build_deliverables.py
```

---

## 📊 Resumen de Resultados Experimentales

| Métrica | 5 términos (Controlador A) | 7 términos (Controlador B) | 9 términos (Controlador C) |
| :--- | :---: | :---: | :---: |
| **Fitness promedio** (5 corridas) | 0.7218 ± 0.0488 | **0.7299 ± 0.0593** | 0.7134 ± 0.0649 |
| **Fitness máximo** (mejor corrida) | **0.7616** (semilla 999) | **0.8199** (semilla 42) | **0.7946** (semilla 999) |
| $OS^+$ (%) | 0.0577 (media: 0.0115 ± 0.0258) | 0.7896 (media: 1.2004 ± 1.3434) | 0.0000 (media: 0.4326 ± 0.9673) |
| $OS^-$ (%) | 0.0000 (media: 0.2439 ± 0.5453) | 0.0000 (media: 0.0000 ± 0.0000) | 1.3638 (media: 1.2498 ± 1.9562) |
| $SSE^+$ (rad) | 0.0031 (media: 0.0390 ± 0.0508) | 0.0063 (media: 0.0213 ± 0.0089) | 0.0144 (media: 0.0879 ± 0.1139) |
| $SSE^-$ (rad) | 0.0104 (media: 0.0344 ± 0.0235) | 0.0060 (media: 0.0379 ± 0.0303) | 0.0122 (media: 0.0478 ± 0.0649) |
| $t_r^+$ (s) | 11.70 (media: 15.90 ± 5.82) | 13.40 (media: 17.50 ± 5.85) | 14.70 (media: 21.80 ± 16.08) |
| $t_r^-$ (s) | 30.40 (media: 21.80 ± 9.01) | 11.70 (media: 14.90 ± 3.99) | 11.30 (media: 18.99 ± 10.64) |
| $t_s^+$ (s) | 16.80 (media: 27.50 ± 15.23) | 17.60 (media: 27.38 ± 10.96) | 18.60 (media: 30.60 ± 17.79) |
| $t_s^-$ (s) | 40.40 (media: 42.26 ± 10.17) | 15.60 (media: 30.45 ± 16.94) | 15.10 (media: 24.36 ± 14.90) |
| **Reglas activas** (mejor / media ± DE) | 16 / 25 (17.4 ± 3.4) | 39 / 49 (35.8 ± 4.1) | 58 / 81 (54.4 ± 7.8) |
| **Número de parámetros optimizados** | 95 genes | 161 genes | 243 genes |
| **Tiempo de optimización (s)** | 169.63 ± 1.47 s | 172.32 ± 0.76 s | 181.87 ± 0.81 s |
| **Tiempo promedio de inferencia (ms)** | 10.065 ± 0.762 ms | 22.761 ± 2.088 ms | 36.585 ± 5.642 ms |
| **Uso de memoria (MB)** | 0.491 ± 0.037 MB | 0.884 ± 0.071 MB | 1.436 ± 0.205 MB |
