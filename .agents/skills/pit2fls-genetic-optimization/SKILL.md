---
name: pit2fls-genetic-optimization
description: Optimización genética de Sistemas Lógicos Difusos Tipo-2 de Intervalo Paramétricos (PIT2FLS) usando operadores de conjunción paramétrica, función de aptitud multiobjetivo transitoria (MOTFF) y supresión de reglas. Basado en "A Feasible Genetic Optimization Strategy for Parametric Interval Type-2 Fuzzy Logic Systems" (IJFS, 2017).
---

# Guía de Optimización Genética para PIT2FLS

Esta guía proporciona el protocolo técnico riguroso para diseñar, optimizar e implementar **Sistemas Lógicos Difusos Tipo-2 de Intervalo Paramétricos (Parametric Interval Type-2 Fuzzy Logic Systems, PIT2FLS)** usando algoritmos genéticos bajo condiciones de ruido blanco en el control de plantas no lineales.

**Fuente de Autoridad:** Arturo Téllez-Velázquez et al., "A Feasible Genetic Optimization Strategy for Parametric Interval Type-2 Fuzzy Logic Systems", *International Journal of Fuzzy Systems*, 2017. (IJFS-D-16-00634_R1)

---

## 1. Diferenciación Fundamental: PIT2FLS vs. IT2FLS Tradicional

### Definición de PIT2FLS
Un **PIT2FLS** extiende un sistema IT2FLS no paramétrico mediante la introducción de un parámetro individual de regla $r_l \in [0, 1]$ en la operación de conjunción de premisas. En lugar de usar una única t-norma fija para todas las reglas:

$$\text{IT2FLS:} \quad \mu_R(x, y) = T(\mu_{A}(x), \mu_{B}(y))$$

El PIT2FLS permite:

$$\text{PIT2FLS:} \quad \mu_R(x, y) = T(\mu_{A}(x), \mu_{B}(y); r_l)$$

donde $T(\cdot, \cdot; r_l)$ es una **t-norma paramétrica** que modifica su comportamiento según el parámetro de regla $r_l$.

### Beneficio Operacional
El parámetro $r_l$ actúa como un **ponderador dinámico** en la máquina de inferencia, permitiendo que cada regla ajuste independientemente la intensidad con la que sus premisas afectan la conclusión. Esto proporciona control fino especialmente útil bajo condiciones de ruido.

---

## 2. La Conjunción Paramétrica: (p)-Suma Monótona

### Justificación: Complejidad Computacional
Las t-normas paramétricas clásicas (Dombi, Hamacher, Yager, Dubois–Prade, Schweizer–Sklar) requieren operaciones exponenciales u complejas (costo $O(\log n)$ a $O(\log \log n)$). Para sistemas de control en tiempo real, especialmente con muchas reglas o hardware limitado, estas operaciones resultan prohibitivas.

La solución propuesta: **(p)-monotone sum**, que requiere solo operaciones aritméticas básicas (costo $O(1)$, máximo una multiplicación).

### Definición Formal

Divídanse el dominio $[0, 1] \times [0, 1]$ en 4 secciones usando un parámetro $p \in [0, 1]$:

```
       b=1 +---+---+
           | D | D |
           | 12| 22|
       p   +---+---+
           | D | D |
           | 11| 21|
       0   +---+---+
           0   p   1    a
```

La (p)-suma monótona se define por casos:

$$T(a, b; p) = \begin{cases}
T_{11}(a, b), & (a \le p) \wedge (b \le p) \\
T_{21}(a, b), & (a > p) \wedge (b \le p) \\
T_{12}(a, b), & (a \le p) \wedge (b > p) \\
T_{22}(a, b), & (a > p) \wedge (b > p)
\end{cases}$$

donde $T_{11}, T_{12}, T_{21}, T_{22}$ son t-normas básicas que cumplen $T_{11} \le T_{12} \le T_{22}$ y $T_{21} \le T_{22}$.

### Caso de Estudio (DC Servomotor)

En el artículo, se propone:

$$T_o(a, b; r) = \begin{cases}
T_d(a, b), & (a \le r) \wedge (b \le r) \quad \text{[Drástica]} \\
T_p(a, b), & \text{en otro caso} \quad \text{[Producto]}
\end{cases}$$

donde:
- $T_d(a, b) = \begin{cases} a, & b=1 \\ b, & a=1 \\ 0, & \text{en otro caso} \end{cases}$ (t-norma drástica)
- $T_p(a, b) = a \cdot b$ (producto algebraico)

**Comportamiento:** Cuando $r = 0$, toda la salida se concentra en $D_{22}$ (producto puro). Cuando $r = 1$, predomina $D_{11}$ (drástica pura).

---

## 3. Función de Aptitud Transitoria Multiobjetivo (MOTFF)

### Necesidad de Parámetros Transitorios
Las métricas de error simplistas (RMSE, ITAE, SSE aislado) no capturan la calidad total de la respuesta dinámica. Un controlador que minimiza error cuadrático puede oscilar severamente o tardar siglos en asentarse.

La propuesta: evaluar **simultáneamente** cuatro parámetros transitorios principales medidos durante la respuesta a un escalón cuadrado.

### Los Cuatro Objetivos

1. **Sobretiro (Overshoot, OS)**: Máximo porcentaje por encima de la referencia después del tiempo de levantamiento.
   $$OS = 100 \times \frac{h_{\text{max}} - h_{\text{ref}}}{h_{\text{ref}}}$$

2. **Error en Estado Estable (Steady-State Error, SSE)**: Magnitud promedio del error después de alcanzar estado estable (típicamente $|e| < 5\%$).

3. **Tiempo de Levantamiento (Rise Time, $t_r$)**: Intervalo entre cuando la respuesta alcanza 10% y 90% de la referencia.

4. **Tiempo de Asentamiento (Settling Time, $t_s$)**: Tiempo necesario para que la respuesta permanezca dentro del rango $\pm 5\%$ de la referencia sin rebasar.

### Fórmula de Aptitud (Ecuación 12 del Paper)

Para el $i$-ésimo individuo de la población GA:

$$f_i = w_1 \frac{1}{1 + |OS_i|} + w_2 \frac{1}{1 + |SSE_i|} + w_3 \frac{t_r^0}{q \cdot t_{r,i}} + w_4 \frac{t_s^0}{t_{s,i}}$$

Sujeto a: $\sum_{j=1}^{4} w_j = 1, \quad w_j \ge 0$

donde:
- **$t_r^0, t_s^0$**: Tiempos teóricos ideales (ej. $t_r^0 = 5$ s, $t_s^0 = 13$ s con voltaje máximo de 5V).
- **$q$**: Factor de penalización que corrige "rise times falsas". Si el rango alcanzado es menor que la referencia:
  $$q = \frac{h'_{\max}}{h_{\max}} \quad \text{donde } h_{\max} = \max(h), \, h'_{\max} = \max(h_{\text{reference}})$$
- **$w_1 = w_2 = w_3 = w_4 = 0.25$**: Pesos iguales (caso estándar con un escalón).
- **Para referencias cuadradas:** $w_j = 0.125$ (8 objetivos: 4 parámetros × 2 semiciclos).

**Rango de Aptitud:** $f_i \in [0, 1]$, donde $f_i = 1$ indica desempeño óptimo en todos los objetivos.

---

## 4. Arquitectura del Algoritmo Genético (GA)

### 4.1 Normalización de Entrada/Salida

Para acotar el espacio de búsqueda a $[-1, 1]$, se aplican transformaciones lineales:

**Escalado de entrada** (dominio físico $\to$ intervalo $[-1, 1]$):
$$x'_i = \frac{2}{R_{x_i}^+ - R_{x_i}^-} x_i - \frac{R_{x_i}^+ + R_{x_i}^-}{R_{x_i}^+ - R_{x_i}^-}$$

**Escalado de salida** (intervalo $[-1, 1] \to$ dominio físico):
$$y_j = \frac{R_{y_j}^+ - R_{y_j}^-}{2} y'_j + \frac{R_{y_j}^+ + R_{y_j}^-}{2}$$

### 4.2 Estructura del Cromosoma (Q)

El cromosoma agrupa **tres genotipos** distintos ordenados secuencialmente:

$$Q = [\underbrace{d_1, d_2, \ldots}_{\text{Distribución de Conjuntos}}, \underbrace{r_1, r_2, \ldots}_{\text{Anchura FOU}}, \underbrace{r_1^{(\ell)}, r_2^{(\ell)}, \ldots, r_L^{(\ell)}}_{\text{Parámetros de Regla}}]$$

donde:
- **$d$**: Parámetros de posición y escala de las funciones de membresía de entrada y salida.
- **$r$ (FOU width)**: Anchura del "Footprint of Uncertainty" (intervalo entre UMF y LMF).
- **$r^{(\ell)}$**: Parámetro específico de cada regla $\ell$, $\in [0, 1]$.

#### Representación Binaria Homogénea
Cada gen se codifica como un **número en punto fijo firmado de 10 bits**:
- 1 bit de signo
- 1 bit entero
- 8 bits fraccionarios

Esta representación garantiza que todos los parámetros se acotan a $[-1, 1]$ y permite concatenación de genes sin conflictos de alineación.

#### Reducción de Dimensionalidad: Discursos Simétricos
En variables cuyo dominio es simétrico respecto al origen (ej. error $e \in [-\pi/2, \pi/2]$, cambio de error $c \in [-\pi/6, \pi/6]$), es recomendable:
- Definir solo los conjuntos en la mitad positiva del dominio.
- Reflejar automáticamente los parámetros hacia la mitad negativa.
- Número de conjuntos: **impar** (para que exista un conjunto "cero" central).

**Resultado para el caso DC servomotor:** Reducción de 48 a 27 genes (ver Tabla 9 del paper).

### 4.3 Operadores Genéticos

#### Selección y Cruzamiento
1. **Selección:** Ruleta proporcional basada en aptitud fitness.
2. **Cruzamiento:** Dos puntos de corte (*two-point crossover*), intercambiando bloques de genotipos completos:
   - Locus 1 a 9: distribución de conjuntos
   - Locus 10 a 18: anchura FOU
   - Locus 19 a 27: parámetros de regla
3. **Elitismo:** El mejor individuo se preserva sin cambios hacia la siguiente generación.

#### Mutación Adaptativa
La probabilidad de mutación se ajusta dinámicamente mediante:

$$p_M = \frac{k}{f_o} \exp(-6 f_o)$$

donde:
- $f_o$ = aptitud del mejor individuo en la población actual.
- $k$ = constante de máximo (típicamente 1).

**Interpretación:** 
- Cuando el mejor individuo es mediocre ($f_o \approx 0$), $p_M$ es alta → mutaciones agresivas.
- Cuando se alcanza buena aptitud ($f_o \to 1$), $p_M \to 0$ → convergencia conservadora.

#### Regeneración Poblacional
Si el **70% de la población es similar (90%) al mejor individuo**, la población se regenera:
- Se conserva el mejor individuo (elitismo).
- Se crean individuos aleatorios nuevos en el 99% restante.
- Evita estancamiento en máximos locales.

### 4.4 Pseudocódigo del Algoritmo GA

```
1. Generar población inicial aleatoria
2. MIENTRAS no se cumpla criterio de parada:
   a) Evaluar aptitud de cada individuo (Eq. 12)
   b) Ordenar población por aptitud descendente
   c) SI 70% de población es similar al mejor (90%):
      - Regenerar población conservando elitista
      SINO:
      - Seleccionar padres por ruleta
      - Cruzar parejas → 2 descendientes
      - Aplicar mutación con probabilidad p_M adaptativa
      - Evaluar aptitud de descendientes
      - Reemplazar peor individuo si nuevo es mejor
3. Retornar mejor solución encontrada
```

---

## 5. Protocolo de Supresión de Reglas Paramétricas

### Objetivo
Identificar qué reglas tienen influencia real en la respuesta del sistema y cuáles pueden simplificarse (parámetro fijo no-paramétrico).

### Metodología

1. **Evaluación de Sensibilidad Individual:**
   - Fijar el parámetro $r_\ell = 1$ (equivalente a usar la t-norma drástica, eliminando toda correlación entre premisas).
   - Registrar cambios en los parámetros transitorios: $\Delta OS, \Delta SSE, \Delta t_r, \Delta t_s$.

2. **Clasificación de Influencia:**
   - **Sin cambio (*unchanged*, "*"):** La regla no afecta ningún parámetro transitorio.
   - **Pequeño cambio ("  "):** Variación marginal observable.
   - **Cambio Grande ("  "):** Variación significativa.

3. **Decisión de Sustitución:**
   - Reglas **sin cambio** → Reemplazar $T_o(\cdot, \cdot; r_\ell)$ por t-norma no-paramétrica fija, típicamente $T_p(a,b) = a \cdot b$ (producto algebraico).
   - Reglas **con cambio significativo** → Mantener paramétrica $T_o(\cdot, \cdot; r_\ell)$.

### Hallazgo Clave (DC Servomotor, Tabla 11, Ruido 50%)
Con 9 reglas en la configuración estándar:
- **Reglas 1–3 y 7–9** (periféricas, error grande): *sin cambio* → Pueden simplificarse a $T_p$.
- **Reglas 4–6** (centrales, error cercano a cero): *cambio significativo* → Deben mantener parámetro $r_\ell$.

**Implicación:** Las decisiones de control críticas ocurren cuando el error es pequeño (comportamiento de estabilización). Las reglas para error grande tienen menos impacto en la robustez frente a ruido.

### Tabla 12 del Paper: Configuración Simplificada

| Voltaje | Error Cambio NC | Error Cambio ZC | Error Cambio PC |
|---------|-----------------|-----------------|-----------------|
| **Error Pos. NE** | $T_p^{(1)}$ | $T_p^{(2)}$ | $T_p^{(3)}$ |
| **Error Pos. ZE** | $T_o^{(4)}$ | $T_o^{(5)}$ | $T_o^{(6)}$ |
| **Error Pos. PE** | $T_p^{(7)}$ | $T_p^{(8)}$ | $T_p^{(9)}$ |

Donde $T_o$ es paramétrica y $T_p$ es no-paramétrica.

---

## 6. Caso de Estudio: Control de Servomotor DC

### 6.1 Especificaciones de la Planta

Función de transferencia (Laplace):
$$G(s) = \frac{H(s)}{V(s)} = \frac{0.5}{s^3 + 13.6667s^2 + 23.3487s}$$

donde:
- $V(s)$ = voltaje aplicado a terminales (entrada).
- $H(s)$ = posición angular del rotor en radianes (salida).

### 6.2 Configuración Fuzzy (MISO)

**Entradas:**
- Error de posición: $e \in [-\pi/2, \pi/2]$ rad
- Cambio de error: $c \in [-\pi/6, \pi/6]$ rad/s

**Salida:**
- Voltaje: $v \in [-8.1819, 8.1819]$ V

**Términos lingüísticos** (3 por variable):
- Error: NE (Negativo), ZE (Cero), PE (Positivo)
- Cambio: NC (Negativo), ZC (Cero), PC (Positivo)
- Voltaje: NV (Negativo), ZV (Cero), PV (Positivo)

**Total de reglas:** $L = 3 \times 3 = 9$ (como en la matriz Mamdani estándar)

### 6.3 Configuración del GA

- **Población inicial:** 50–100 individuos
- **Generaciones máximas:** 100–500 (ajustar según convergencia)
- **Probabilidad de cruzamiento:** 65%
- **Probabilidad de mutación:** Adaptativa (Eq. 17, rango 2–10%)
- **Función de aptitud:** MOTFF (Eq. 12) con $w_1 = w_2 = w_3 = w_4 = 0.25$
- **Pesos temporales ideales:** $t_r^0 = 5$ s, $t_s^0 = 13$ s

### 6.4 Resultados Experimentales (Ruido 0%, 5%, 10%, 30%, 50%)

Según la Tabla 10 del paper, PIT2FLS muestra ventaja sobre T1FLS conforme aumenta el ruido:

| Ruido (%) | Sistema | Aptitud | OS (%) | SSE (rads) | $t_r$ (s) | $t_s$ (s) |
|:---------:|:-------:|:-------:|:------:|:----------:|:---------:|:---------:|
| 0 | PIT2 | 0.9882 | 0.0018 | 0.000022 | 9.0 | 13.0 |
| 0 | T1 | 0.9680 | 0.0013 | 0.0043 | 9.0 | 14.5 |
| 50 | PIT2 | 0.9601 | 0.0011 | 0.0036 | 9.3 | 13.5 |
| 50 | T1 | 0.8797 | 0.0077 | 0.0013 | 10.7 | 17.5 |

**Observación clave:** A ruido extremo (50%), PIT2FLS mantiene asentamiento en ~13.5 s, mientras T1FLS se degrada a 17.5 s. Simultáneamente, PIT2FLS logra menor sobretiro (0.0011 vs. 0.0077).

---

## 7. Lista de Verificación Anti-Alucinación

Antes de aplicar este skill, verificar:

- [ ] ¿Se usó la (p)-suma monótona con solo multiplicación como operación más compleja?
- [ ] ¿Todos los genes están en $[-1, 1]$ o $[0, 1]$ (sin negativas para parámetros de regla)?
- [ ] ¿La función de aptitud incluye explícitamente los 4 parámetros transitorios (OS, SSE, $t_r$, $t_s$)?
- [ ] ¿Se aplicó el factor de penalización $q$ (Ec. 13) para evitar "rise times falsas"?
- [ ] ¿Se especificó que $G(s) = \frac{0.5}{s^3 + 13.6667s^2 + 23.3487s}$?
- [ ] ¿La supresión se basa en comparar respuesta con $r_\ell = 1$ (drástica), no en perturbación?
- [ ] ¿Se confirmó que las reglas centrales (4–6, error cercano a cero) retienen parámetricidad?
- [ ] ¿Se documentó el número exacto de genes reducidos por simetría?
- [ ] ¿Se evitaron afirmaciones sobre IT2FLS no comparadas en el paper?
- [ ] ¿Toda afirmación cuantitativa (porcentajes, tiempos) proviene de Tablas 5–13 del paper?

---

## 8. Complementariedad con la Skill "fuzzy-logic-expert"

Esta skill **complementa** la guía `fuzzy-logic-expert`:

| Tema | fuzzy-logic-expert | pit2fls-genetic-optimization |
|------|:------------------:|:----------------------------:|
| **Fundamentos (T-normas, S-normas)** | Completo | Referencia |
| **Conjuntos Difusos Tipo-1** | Completo | No aplicable |
| **Conjuntos Difusos Tipo-2 General** | Parcial | Construcción UMF/LMF paramétrica |
| **Operador de Conjunción Paramétrica** | No | **Focal: (p)-monotone sum** |
| **Defuzzificación (COA, MOM, etc.)** | Completo | Usa COA estándar |
| **Algoritmo Genético** | No | **Focal: estructura cromosómica, GA adaptativo** |
| **Control Multitransitorio (MOTFF)** | No | **Focal: aptitud basada en dinámicos** |
| **Supresión de Reglas** | No | **Focal: análisis de sensibilidad** |

**Recomendación de uso:** Consulta `fuzzy-logic-expert` para revisar axiomas de t-normas y defuzzificación. Usa esta skill para todo lo relativo a optimización genética, parametrización y robustez bajo ruido.

---

*Fin de Guía PIT2FLS-GA*
