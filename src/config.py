"""Configuración y constantes obligatorias del proyecto (Parcial 2).

Todas las constantes definidas aquí respetan estrictamente las restricciones
obligatorias de `Parcial 2.pdf` y las ecuaciones (10), (12) y (13) de
Téllez-Velázquez et al. (2017), Int. J. Fuzzy Syst., DOI 10.1007/s40815-017-0307-0.
"""

import numpy as np

# 1. Planta del servomotor de CD (Parcial 2.pdf, págs. 1-2, 12; Artículo Ec. 10)
PLANT_NUM = [0.5]
PLANT_DEN = [1.0, 13.6667, 23.3487, 0.0]

# 2. Parámetros obligatorios de simulación (Parcial 2.pdf, págs. 3-4, 12)
T_SIM = 200.0          # Horizonte temporal exacto [s]
DT = 0.10              # Paso temporal [s] (frecuencia de muestreo: 10 Hz, 2001 muestras en [0, 200] s)
X0 = [0.0, 0.0, 0.0]   # Condiciones iniciales obligatorias
REF_PERIOD = 100.0     # Período de la onda cuadrada [s]
REF_AMPLITUDE = 1.0    # Amplitud ±1 [rad]

# 3. Universos de discurso obligatorios y fijos (Parcial 2.pdf, págs. 4-5, 13)
ERROR_MIN = -np.pi / 2.0
ERROR_MAX = np.pi / 2.0

DERROR_MIN = -np.pi / 6.0
DERROR_MAX = np.pi / 6.0

VOLTAGE_MIN = -8.18
VOLTAGE_MAX = 8.18

UNIVERSE_RESOLUTION = 1000  # np.linspace(..., 1000) según ejemplo pág. 13

# 4. Constantes obligatorias de la función fitness (Parcial 2.pdf, págs. 6-7; Artículo Ec. 12)
TR0 = 9.0   # Tiempo de crecimiento de referencia [s]
TS0 = 13.0  # Tiempo de establecimiento de referencia [s]

# Ponderaciones de los 8 objetivos (w1 + w2 + ... + w8 = 1.0; Artículo pág. 10)
FITNESS_WEIGHTS = (0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125)

# Ventanas de evaluación de transiciones (descartando [0, 50) s de 0 -> +1)
# Transición Positiva (-1 -> +1): t in [100, 150) s
# Transición Negativa (+1 -> -1): t in [150, 200] s (y [50, 100) s disponible para verificación)
POS_TRANSITION_WINDOW = (100.0, 150.0)
NEG_TRANSITION_WINDOW = (150.0, 200.0)
FIRST_NEG_TRANSITION_WINDOW = (50.0, 100.0)

# 5. Configuraciones de controladores difusos Mamdani obligatorias (Parcial 2.pdf, págs. 3, 8)
CONTROLLER_CONFIGS = {
    "A": {"n_terms": 5, "label": "Controlador A (5 términos)"},
    "B": {"n_terms": 7, "label": "Controlador B (7 términos)"},
    "C": {"n_terms": 9, "label": "Controlador C (9 términos)"},
}

LINGUISTIC_LABELS = {
    5: ["NB", "NS", "ZE", "PS", "PB"],
    7: ["NB", "NM", "NS", "ZE", "PS", "PM", "PB"],
    9: ["NVB", "NB", "NM", "NS", "ZE", "PS", "PM", "PB", "PVB"],
}

# 6. Configuración mínima obligatoria de PyGAD y repetibilidad (Parcial 2.pdf, págs. 8-9, 14)
SOL_PER_POP = 20
NUM_GENERATIONS = 30
NUM_PARENTS_MATING = 10
KEEP_ELITISM = 2
CROSSOVER_TYPE = "two_points"
CROSSOVER_PROBABILITY = 0.8
MUTATION_TYPE = "random"
MUTATION_PROBABILITY = 0.15

# 5 semillas aleatorias distintas para las 5 ejecuciones independientes (Fase 5)
EXPERIMENT_SEEDS = [42, 100, 2026, 777, 999]

