# Aclaraciones solicitadas y su trazado en el código

En el desarrollo del proyecto **OMSDMAG** se han solicitado cuatro aclaraciones respecto a la implementación.  A continuación se enumeran dichas aclaraciones, se muestra **dónde están cubiertas en el código fuente** (archivo y número de línea aproximado) y se incluye una breve explicación de cómo verificarlas.

---

## 1️⃣ Sobre‑impulso (OS) expresado en porcentaje

- **Requisito:**   El sobre‑impulso debe reportarse como **%** tal como la Tabla 10 del artículo.
- **Implementación:**   En `src/metrics_fitness.py`.
    - Docstring de módulo (líneas **7‑9**) indica explícitamente que *OS se expresa en porcentaje (%)*.
    - En la función `compute_step_metrics` (líneas **170‑174**) se calcula:
    ```python
    directional_excess = step_dir * (y_win - r_final)
    max_excess = float(np.max(directional_excess))
    os_pct = 100.0 * max(0.0, max_excess / abs(r_final))
    ```
    - El valor retornado en el diccionario tiene la clave `"OS"` y ya está en **porcentaje**.
- **Cómo comprobarlo:**
    ```bash
    uv run python -c "import src.metrics_fitness as mf; import numpy as np;\
    print(mf.compute_step_metrics(np.arange(0,200,0.1), np.sin(np.arange(0,200,0.1)), 100,150,-1,1)['OS'])"
    ```
    La salida será un número del tipo `xx.x` que corresponde al % de sobre‑impulso.

---

## 2️⃣ Factor de penalización **q** (ecuación 13)

- **Requisito:**   El factor `q` (ρ) está descrito en la página 10, columna 2, párrafo 1 del artículo y su ecuación 13.
- **Implementación:**   En `src/metrics_fitness.py` – función `compute_penalty_factor_q`.
    - Docstring (líneas **33‑44**) reproduce literalmente la definición del artículo.
    - Línea **45** menciona el *piso* `q >= 1.0`.
    - Cálculo literal de la ecuación 13 en la línea **72**:
    ```python
    q_eq13 = (float(h0_max) - h_min) / denom
    return float(max(q_eq13, 1.0))
    ```
- **Cómo comprobarlo:**
    ```bash
    uv run python -c "import src.metrics_fitness as mf; import numpy as np;\
    print(mf.compute_penalty_factor_q(np.array([0.2,0.6,0.9])))"
    ```
    El resultado será ≥ 1.0.

---

## 3️⃣ Uso estricto de `scipy.signal.lsim`

- **Requisito:**   La simulación del servomotor debe hacerse **exclusivamente** con `lsim`.
- **Implementación:**   En `src/plant_sim.py`.
    - Cabecera del archivo (líneas **1‑5**) indica que la simulación es “estricta con `scipy.signal.lsim`”.
    - En el cuerpo del método `simulate` (líneas **58‑68**, **112‑123**, **211‑223**) se invoca:
    ```python
    tout, theta, xout = lsim(self.G, U=u, T=self.t, X0=self.x0, interp=False)
    ```
    - Además, la variable `lsim_consistency_error` verifica que la simulación paso‑a‑paso coincida con la llamada global, con tolerancia < 1e‑9.
- **Cómo comprobarlo:**
    ```bash
    uv run python -c "from src.plant_sim import PlantSimulator; p=PlantSimulator();\
    res=p.simulate(); print('lsim_consistency_error =', res['lsim_consistency_error'])"
    ```
    Debería mostrarse un número muy cercano a `0.0`.

---

## 4️⃣ Funciones de membresía triangulares y orden `a < b < c`

- **Requisito:**   Los MF (tanto de entrada como de salida) deben ser triangulares y el algoritmo genético debe garantizar **a < b < c** en todo momento.
- **Implementación:**
    - **Definición y reparación** está en `src/chromosome.py` – función `_decode_variable_mfs`.
        - Docstring (líneas **6‑10**) menciona explícitamente que los MF son triangulares y que se asegura `a < b < c`.
        - Código (líneas **116‑127**, **188‑190**) fuerza el orden estricto y devuelve un `penalty` cuando se aplican reparaciones.
    - **Construcción de los MF** en el controlador (`src/fuzzy_controller.py`):
        - Cuando `use_automf_baseline=False` (líneas **93‑102**) se llama a `fuzz.trimf` con los parámetros devueltos por el decodificador, que ya cumplen la condición de orden.
- **Cómo comprobarlo:**
    ```bash
    uv run python -c "from src.chromosome import create_baseline_chromosome, decode_chromosome;\
    c=create_baseline_chromosome(5); d=decode_chromosome(c,5);\
    print('error MF[0]:',d['error_mfs'][0])"
    ```
    Cada MF será una tupla `[a,b,c]` con `a < b < c`.
    Además, la función de decodificación devuelve un `penalty` > 0 cuando alguna regla se reparó, lo que puede observarse añadiendo `print(penalty)` durante la evolución.

---

## 📚 Resumen rápido de dónde está cada pieza
| Aclaración | Archivo | Función / sección | Línea(s) |
|------------|---------|-------------------|----------|
| OS en % | `src/metrics_fitness.py` | `compute_step_metrics` | 170‑174 |
| Factor q | `src/metrics_fitness.py` | `compute_penalty_factor_q` | 33‑45 |
| `lsim` estricto | `src/plant_sim.py` | `simulate` (y helpers) | 58‑68, 112‑123, 211‑223 |
| MF triangulares & orden `a<b<c` | `src/chromosome.py` | `_decode_variable_mfs` | 116‑127, 188‑190 |
| Aplicación de MF al controlador | `src/fuzzy_controller.py` | bucle de creación MF | 93‑102 |

---

## ✅ Verificación rápida de todo el proyecto
```bash
# 1. Sincronizar entorno (incluye PyTorch opcional para la GPU)
uv sync --group cuda

# 2. Ejecutar pruebas unitarias (confirma lsim, q, OS, MF)
uv run python -m tests.test_verification

# 3. Ejecutar una corrida de ejemplo y observar los valores
uv run python -c "\
    from src.plant_sim import PlantSimulator;\
    from src.fuzzy_controller import MamdaniFuzzyController;\
    p=PlantSimulator();\
    ctrl=MamdaniFuzzyController(n_terms=5);\
    res=p.simulate(controller=ctrl);\
    print('OS % =',res['metrics']['OS']);\
    print('q =',res['metrics']['q']);\
    print('lsim_consistency_error =',res['lsim_consistency_error']);\
    "
```
Si todas las salidas son coherentes (OS en porcentaje, q ≥ 1, error ≈ 0), las aclaraciones están correctamente implementadas.

---

**Esta hoja (`docs/ACLRACIONES.md`) sirve como referencia para revisores, docentes y para cualquier persona que necesite localizar rápidamente la parte del código que satisface cada una de las exigencias del enunciado.**
