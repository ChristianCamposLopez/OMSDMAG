# Optimización Multiobjetivo de Sistemas Difusos Mamdani mediante Algoritmos Genéticos (OMSDMAG)

Proyecto de investigación y desarrollo para el diseño y optimización de controladores difusos tipo Mamdani aplicados al control de posición angular de un servomotor de corriente directa (DC). Basado en el documento de requerimientos **Parcial 2** y el artículo científico de referencia (*IJFS-D-16-00634_R1*).

---

## 📋 Descripción del Proyecto

El proyecto implementa un entorno riguroso, reproducible y modular en Python para:
1. **Modelar y simular** la dinámica de un servomotor DC de tercer orden:
   $$G(s) = \frac{0.5}{s^3 + 13.6667 s^2 + 23.3487 s}$$
2. **Implementar controladores difusos Mamdani** con 5, 7 y 9 funciones de pertenencia triangulares por variable de entrada ($e$, $\dot{e}$) y de salida ($u$), con universos de discurso acotados:
   - Error: $e \in [-\pi/2, \pi/2]$ rad
   - Cambio de error: $\dot{e} \in [-\pi/6, \pi/6]$ rad/s
   - Voltaje: $u \in [-8.18, 8.18]$ V
3. **Optimizar cromosomas genéticos** con PyGAD optimizando simultáneamente:
   - Los centros de las funciones de pertenencia intermedias preservando orden estricto mediante distancias relativas.
   - Banderas de activación/desactivación de reglas.
   - Consecuentes lingüísticos de cada regla.
4. **Evaluar una función de aptitud multiobjetivo** compuesta por 8 métricas de desempeño sobre una referencia cuadrada periódica ($\pm 1$ rad, $T = 100$ s) a lo largo de un horizonte de $200$ s:
   - $IAE$, $ITAE$, Sobrepaso positivo ($OS^+$), Sobrepaso negativo ($OS^-$), Tiempo de subida ($t_r$), Tiempo de establecimiento ($t_s$), Error en estado estacionario ($e_{ss}$) y Variación de la acción de control ($\Delta u$).
5. **Generar análisis estadístico**, tablas comparativas, figuras de alta resolución, informe ejecutable Jupyter Notebook y reporte formal en Microsoft Word.

---

## 🗂️ Estructura del Repositorio

```text
├── Parcial 2.pdf                                 # Documento rector de requerimientos
├── IJFS-D-16-00634_R1.pdf                        # Artículo científico de referencia
├── Parcial2_ComputacionFlexible.ipynb            # Notebook interactivo con celdas ejecutadas y reporte
├── Reporte_Parcial2_ComputacionFlexible.docx     # Reporte académico formal en formato Word
├── main.py                                       # Script CLI ejecutable para reproducir todo
├── build_deliverables.py                         # Generador automatizado del notebook y docx
├── src/                                          # Código fuente modular
│   ├── config.py                                 # Parámetros, constantes y universos
│   ├── plant_sim.py                              # Modelo LTI y simulación del servomotor
│   ├── fuzzy_controller.py                       # Controlador Mamdani y superficie de control
│   ├── chromosome.py                             # Codificación, decodificación y mapeo genético
│   ├── metrics_fitness.py                        # Métricas transitorias, fitness y penalizaciones
│   ├── ga_optimizer.py                           # Integración y optimización con PyGAD
│   └── plotting_tables.py                        # Generación de gráficas y tablas
├── tests/                                        # Suite de pruebas unitarias y de verificación
│   └── test_verification.py                      # Verificación matemática y de componentes
└── results/                                      # Resultados experimentales
    ├── baselines/                                # Métricas de controladores base (5, 7, 9)
    ├── runs/                                     # 15 ejecuciones genéticas (5 semillas x 3 conf.)
    ├── figures/                                  # Gráficas generadas en PNG (300 DPI)
    └── tables/                                   # Tablas comparativas (Markdown y CSV)
```

---

## 🚀 Instalación y Requisitos

Se requiere Python 3.10 o superior (compatible con Python 3.14). Se recomienda el uso de un entorno virtual:

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# En Linux/macOS:
source venv/bin/activate

# Instalar dependencias necesarias
pip install numpy scipy scikit-fuzzy pygad matplotlib nbclient python-docx pypdf
```

---

## 🧪 Ejecución y Pruebas

### 1. Ejecutar la suite de pruebas unitarias
```bash
python -m unittest tests/test_verification.py -v
```

### 2. Ejecutar la simulación completa y optimización CLI
```bash
# Modo rápido de prueba (pocas generaciones para validación rápida)
python main.py --mode test

# Modo completo (ejecuta las 15 optimizaciones con 5 semillas cada una)
python main.py --mode full
```

### 3. Regenerar el Notebook y el Reporte Word
```bash
python build_deliverables.py
```

---

## 📊 Principales Resultados

- **Reducción de IAE:** Las optimizaciones genéticas lograron reducciones notables respecto a los controladores basales sin sintonizar.
- **Transiciones Asimétricas:** Se evaluaron por separado las transiciones positivas ($0 \to 1$ rad) y negativas ($1 \to -1$ rad) para asegurar un control balanceado y sin sesgo direccional.
- **Superficie de Control Suavizada:** La optimización de reglas y centros redujo el esfuerzo de control $\Delta u$, minimizando oscilaciones espurias y saturación en los límites del actuador ($\pm 8.18$ V).

---

## 👤 Autor
**Christian Campos López**  
Universidad Tecnológica de la Mixteca (UTM)  
Contacto: `calc020926@gs.utm.mx`
