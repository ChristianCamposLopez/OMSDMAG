# Las 30 preguntas del profesor y sus respuestas (Parte 5 del Parcial 2)

Cada pregunta aparece tal como la da el profesor en el enunciado, seguida de una
respuesta breve, clara y pedagógica. Las pocas cifras que se citan provienen de los
experimentos del proyecto; se actualizarán con la campaña final regenerada
(`uv run python main.py --force`), aunque las conclusiones de fondo no cambian.

---

## 1. ¿Mayor fitness pero 10× más tiempo de optimización es la mejor solución?

> **Pregunta original:** 1. Si el controlador de 9 términos lingüísticos obtiene el mayor
> fitness de todos los experimentos, pero requiere diez veces más tiempo de optimización
> que el controlador de 5 términos, ¿puede afirmarse que es la mejor solución?
> Justifique utilizando evidencia experimental.

**Respuesta:** No se puede afirmar solo por el fitness. La mejor solución equilibra
desempeño y costo, así que la mejora tendría que ser real y no fruto de la suerte de una
corrida (para eso están las 5 ejecuciones con su desviación estándar). En nuestros
experimentos, además, la premisa del "10×" no se cumple: el tiempo de optimización real
solo creció ≈ 7 % (de ≈ 170 s a ≈ 182 s), así que la decisión de cuál es "mejor" se
resuelve comparando el fitness con su incertidumbre y con los demás costos, no por un
solo número.

## 2. ¿Más términos lingüísticos siempre mejoran el desempeño?

> **Pregunta original:** 2. Muchos estudiantes asumen que incrementar el número de
> términos lingüísticos siempre mejora el desempeño del controlador. ¿Sus resultados
> experimentales respaldan esta afirmación? Explique.

**Respuesta:** No. Con 5, 7 y 9 términos el fitness promedio fue prácticamente el mismo
(0.722, 0.730 y 0.713), sin una mejora clara ni constante al aumentar los términos. La
razón es que más términos también hacen más grande y más difícil el problema de
búsqueda: con el mismo esfuerzo de optimización, el algoritmo "diluye" su atención entre
más opciones. Más términos dan más capacidad de expresión al controlador, pero no una
garantía de mejor control.

## 3. Efecto del número de términos sobre espacio de búsqueda, parámetros y dificultad

> **Pregunta original:** 3. ¿Qué efecto tiene el aumento del número de términos
> lingüísticos sobre: el tamaño del espacio de búsqueda, el número de parámetros
> optimizables, y la dificultad del proceso de optimización?

**Respuesta:** Los tres efectos van en la misma dirección: más términos hacen todo más
grande y más difícil. Las combinaciones posibles de reglas pasan de ≈ 10¹⁹ (5 términos)
a ≈ 10⁴⁴ (7) y a ≈ 10⁸¹ (9): un salto astronómico en el "mapa" donde busca el algoritmo.
Los parámetros por controlador también crecen (95, 161 y 243 genes) y, como el número de
intentos de optimización es igual para los tres, hay menos intentos por opción: la
búsqueda se vuelve más difícil y con más probabilidad de quedarse en soluciones
intermedias.

## 4. Mismo fitness, menos de la mitad de las reglas: ¿cuál preferir?

> **Pregunta original:** 4. Si dos controladores presentan prácticamente el mismo fitness
> final pero uno utiliza menos de la mitad de las reglas activas, ¿cuál debería
> preferirse? Justifique.

**Respuesta:** El que usa menos reglas. Si el desempeño medido es el mismo, el sistema
más pequeño es mejor: responde más rápido (en nuestros experimentos, la inferencia pasó
de ≈ 10 ms a ≈ 37 ms al crecer de 5 a 9 términos), consume menos memoria y es más fácil
de entender y mantener por una persona. Es el principio de que, a igual resultado, la
solución más simple es la mejor.

## 5. ¿Más reglas implican necesariamente mejor capacidad de control?

> **Pregunta original:** 5. ¿Un mayor número de reglas implica necesariamente una mejor
> capacidad de control? Utilice resultados experimentales para sustentar su respuesta.

**Respuesta:** No. En los experimentos, la proporción de reglas que el algoritmo decide
mantener activas se quedó casi constante (67–73 %) sin importar el número de términos, y
la relación entre cuántas reglas hay y qué tan buen fitness se obtiene resultó débil.
Lo que importa no es la cantidad, sino *cuáles* reglas están activas y qué tan bien
calzadas están las funciones de membresía: reglas de más pueden solo sumar costo sin
mejorar la respuesta.

## 6. Reglas eliminadas por el GA con mejora del fitness: ¿qué concluir?

> **Pregunta original:** 6. Si durante la optimización genética algunas reglas son
> eliminadas y el fitness mejora, ¿qué puede concluir acerca de dichas reglas?

**Respuesta:** Que eran redundantes o estorbaban: su efecto ya lo cubrían las reglas
vecinas, o interferían con el control. El algoritmo las descartó porque no ayudaban.
Eso sí, una conclusión rigurosa exige verificación: para afirmar que fueron eliminadas
"por inútiles" (y no por casualidad del azar) se hace la prueba de ablación, que consiste
en apagar y encender cada regla del mejor controlador y medir cuánto cambia el fitness.

## 7. ¿Reglas importantes a simple vista pueden volverse irrelevantes?

> **Pregunta original:** 7. ¿Es posible que algunas reglas consideradas intuitivamente
> importantes resulten irrelevantes durante la optimización? Explique por qué.

**Respuesta:** Sí, porque la utilidad de una regla depende del contexto. Cuando el
algoritmo reacomoda las funciones de membresía, cambia la "zona de actuación" de cada
regla: una regla que parecía clave puede quedar cubierta por las reglas vecinas o dejar
de revisitar la zona donde actuaba. En nuestro proyecto pasó con las reglas de error
grande: parecen importantes (el error llega hasta 2 rad), pero el control efectivo lo
logran las reglas de error moderado con cambio de error grande, así que las primeras
pueden sobrar.

## 8. Mínimo overshoot pero máximo tiempo de establecimiento: ¿es superior?

> **Pregunta original:** 8. Suponga que un controlador obtiene el menor overshoot de
> todos los experimentos, pero también el mayor tiempo de establecimiento. ¿Puede
> considerarse superior? Justifique.

**Respuesta:** No, no por sí solo. Sobrepaso pequeño y establecimiento lento son dos
caras del mismo compromiso: un controlador muy "cauteloso" apenas rebasa, pero tarda en
quedarse en el objetivo. La función fitness evalúa las dos cosas con pesos separados,
así que lo que decide es el promedio ponderado del conjunto: un extremo bueno puede
convivir con otro extremo malo, y entonces ese controlador no es superior, solo distinto.

## 9. ¿Por qué el fitness considera OS, SSE, tr y ts y no solo SSE?

> **Pregunta original:** 9. ¿Por qué la función fitness utilizada en este examen
> considera simultáneamente overshoot, SSE, rise time y settling time, en lugar de
> utilizar únicamente SSE?

**Respuesta:** Porque cada medida detecta una falla diferente: el overshoot detecta
cuánto se pasa del objetivo, el SSE qué tan preciso queda al final, el rise time qué tan
rápido reacciona y el settling time qué tan bien se asienta sin seguir oscilando. Solo
con SSE, un controlador que rebota mucho o tarda eternidades pero termina en el lugar
correcto parecería excelente. Combinarlas obliga a que la respuesta sea rápida, precisa
y estable a la vez.

## 10. Problemas de usar únicamente SSE

> **Pregunta original:** 10. ¿Qué problemas aparecerían si la función fitness utilizara
> únicamente SSE como criterio de evaluación?

**Respuesta:** Aparecerían controladores "estafadores": podrían oscilar mucho al principio,
rebasar el objetivo varias veces o llegar tarde, y aun así ganar, mientras terminen
cerca del valor correcto al final de la ventana. Como el SSE solo mira el error promedio
del final, no estaría viendo el sobrepaso, ni la lentitud, ni las oscilaciones, y el
algoritmo genético se encargaría de explotar ese hueco.

## 11. Problemas de usar únicamente RMSE

> **Pregunta original:** 11. ¿Qué problemas aparecerían si la función fitness utilizara
> únicamente RMSE como criterio de evaluación?

**Respuesta:** El RMSE promedia el error de toda la respuesta, así que un picoteo breve
malhechor se "diluye" entre muchos instantes buenos: queda casi ciego al transitorio.
Un sistema con un sobrepaso grande de unas pocas muestras puntuaría casi igual que uno
curado; y como tampoco mide amortiguamiento, podría preferir respuestas temblorosas que
morirían en la vida real. En corto: pierde la información de *cómo* llega la respuesta,
que es justo lo que este examen quiere evaluar.

## 12. Ventajas del factor de penalización q (Ecuación 13)

> **Pregunta original:** 12. ¿Qué ventajas aporta la incorporación del factor de
> penalización q de la Ecuación (13)? Explique utilizando ejemplos observados durante la
> optimización.

**Respuesta:** q detecta a los tramposos de la velocidad. Si una respuesta nunca alcanza
la referencia (se queda a media distancia), su "tiempo de crecimiento" puede verse
minúsculo y ganador; q lo castiga inflando ese tiempo en la fórmula. En la optimización
se vieron casos claros: respuestas prácticamente planas reciben q ≥ 10⁵ (quedan anuladas)
y una corrida fallida con tr = 50 s recibió q = 1.165, lo que hundió su fitness. Sin q,
el algoritmo premiaría respuestas que no controlan nada pero "llegan rápido" a mitad de
camino.

## 13. Verificaciones ante un individuo con rise time diminuto

> **Pregunta original:** 13. Suponga que durante la optimización aparece un individuo con
> un tiempo de crecimiento extremadamente pequeño. ¿Qué verificaciones adicionales deben
> realizarse antes de considerar que realmente es una buena solución?

**Respuesta:** Verificar que de verdad llegó: que la respuesta sí cruzó la referencia
(el factor q debe quedar en su valor normal, y el código exige cruzar el 90 % del
cambio), que se asentó dentro de la banda del 5 % sin cortarse por el fin de la ventana,
y que las demás métricas (sobrepaso, SSE, settling de ambas direcciones) no están
arruinadas. También conviene mirar la curva: un tiempo minúsculo con voltajes pegados al
límite de 8.18 V es una solución violenta y frágil, no buena.

## 14. ¿Por qué evaluar −1→+1 y también +1→−1 y no solo un escalón?

> **Pregunta original:** 14. ¿Por qué este examen exige evaluar la transición −1→+1 y
> también +1→−1 en lugar de utilizar únicamente una señal escalón?

**Respuesta:** Porque la señal cuadrada obliga al controlador a las dos cosas que hace
en la vida real: acelerar en una dirección y frenar en la opuesta, y ambas no se
comportan igual. Con solo un escalón se vería media historia: un controlador puede salir
perfecto hacia un lado y llegar mal o temblar al regresar, y ese defecto jamás aparecería.
El enunciado lo pide explícitamente: no se acepta evaluar solo una parte de la simulación.

## 15. Qué quedaría sin ver si solo se evaluara la transición positiva

> **Pregunta original:** 15. Si solamente se evaluara la transición positiva, ¿qué
> comportamientos potencialmente problemáticos podrían pasar desapercibidos?

**Respuesta:** Todo lo que ocurre en el camino de regreso: el sobrepaso y el
establecimiento en dirección negativa, los ciclos o zonas muertas que aparecen solo al
frenar, y las asimetrías del controlador (su regla de decisión no es simétrica, así que
puede comportarse distinto según el signo del error). Un sesgo de precisión hacia un
lado podría quedar oculto y el controlador pasaría por "excelente" funcionando a medias.

## 16. ¿Puede existir sobreajuste en un sistema difuso optimizado con GA?

> **Pregunta original:** 16. ¿Puede existir sobreajuste en un sistema difuso optimizado
> mediante algoritmos genéticos? Explique cómo podría manifestarse en este problema
> específico.

**Respuesta:** Sí, aunque en este examen (sin ruido) toma otra forma: el algoritmo puede
afinarse demasiado a los detalles exactos de la simulación de medición, como los
instantes de conmutación o los umbrales del fitness. Se notaría como un controlador con
fitness altísimo pero de comportamiento raro fuera de ese escenario exacto: voltajes
pegados al límite, reglas que solo actúan en los puntos medidos o respuestas que se
deterioran ante cualquier variación. Por eso el reporte discute la robustez y no solo el
valor del fitness.

## 17. Fitness estancado tras 30 generaciones: al menos tres explicaciones

> **Pregunta original:** 17. Suponga que después de 30 generaciones el fitness deja de
> mejorar. ¿Qué posibles explicaciones existen? Mencione al menos tres.

**Respuesta:** Tres causas típicas: (1) la población adoptó ya un mismo tipo de solución
y el algoritmo quedó atrapado en un óptimo local, sin poder salir; (2) el espacio de
búsqueda es enorme y 30 generaciones no alcanzan a recorrerlo más; (3) se perdió la
diversidad: selección fuerte más élite redujeron la población a copias del mejor, y sin
variedad, el cruce ya no produce nada nuevo. En general: más esfuerzo igual no
necesariamente compra progreso.

## 18. ¿Duplicar la población garantiza una mejor solución?

> **Pregunta original:** 18. Si se duplicara el tamaño de la población del algoritmo
> genético: ¿estaría garantizado encontrar una mejor solución? Justifique.

**Respuesta:** No hay garantía; solo más probabilidad. Con el doble de individuos hay más
"intentos" por generación y es más fácil topar con buenas regiones, pero el proceso sigue
siendo azaroso y además el costo se duplica, porque cada evaluación exige una simulación
completa de 200 s. Si el verdadero cuello es el número de generaciones o la pérdida de
diversidad, más población no resuelve nada: mejora gradual, no promesa.

## 19. ¿Duplicar las generaciones garantiza una mejor solución?

> **Pregunta original:** 19. Si se duplicara el número de generaciones: ¿estaría
> garantizado encontrar una mejor solución? Justifique.

**Respuesta:** Tampoco. Más generaciones significan más oportunidades de mejora, pero si
la población ya se estancó (pregunta 17), generar más solo repite lo mismo; y el riesgo
de caer en un óptimo local sigue ahí. Además el tiempo de optimización se duplica.
Un resultado global garantizado exigiría explorar todo el espacio, algo inviable cuando
hay 10⁸¹ combinaciones de reglas posibles.

## 20. ¿Por qué la mutación es necesaria si produce individuos peores?

> **Pregunta original:** 20. Durante la optimización genética pueden aparecer individuos
> claramente peores que sus padres. ¿Por qué la mutación sigue siendo necesaria?

**Respuesta:** Porque sin mutación no hay material nuevo: el cruce solo mezcla lo que ya
existe, y tarde o temprano la población se uniforma y la búsqueda muere. La mutación es
el que introduce sorpresas, algunas buenas y muchas malas. Que nazcan individuos peores
no es un problema: la selección los descarta y conserva a los buenos. Los malos son el
"precio" que se paga por poder explorar.

## 21. ¿Qué aporta el tiempo de establecimiento que no da el tiempo de crecimiento?

> **Pregunta original:** 21. ¿Qué información proporciona el tiempo de establecimiento
> que no proporciona el tiempo de crecimiento?

**Respuesta:** El rise time solo mide la carrera inicial: cuánto tarda en pasar del 10 %
al 90 % del objetivo. El settling time mide algo distinto: cuánto tarda la respuesta en
*seguir quieta* dentro de una banda pequeña de tolerancia. Por eso detecta lo que el
rise time no ve: oscilaciones suaves alrededor del objetivo, rebotes tardíos y a aquella
respuesta que llega rápido pero no se queda. En una frase: el rise time mide cuándo
llega; el settling time mide cuándo se queda.

## 22. Mismas métricas, 3× inferencia: ¿cuál en una aplicación industrial?

> **Pregunta original:** 22. Dos controladores presentan exactamente los mismos valores
> de overshoot, SSE, rise time y settling time, pero uno requiere tres veces más tiempo
> de inferencia. ¿Cuál utilizaría en una aplicación industrial real? Justifique.

**Respuesta:** El más rápido de inferencia. Si el desempeño medido es idéntico, el tiempo
de inferencia representa el costo operativo: se paga en cada instante de control, durante
toda la vida del equipo, y consume margen de cómputo que en la industria se prefiere
reservar para seguridad y diagnóstico. Pagar tres veces más por exactamente lo mismo no
tiene sustento: el controlador simple gana por igual desempeño a menor costo.

## 23. Mejora de 1 % con 4×/8×/3× más recursos: ¿es significativa?

> **Pregunta original:** 23. Suponga que el controlador con 9 términos mejora el fitness
> promedio únicamente un 1 % respecto al controlador de 5 términos, pero requiere cuatro
> veces más memoria, ocho veces más tiempo de optimización y tres veces más tiempo de
> inferencia. ¿Considera que dicha mejora es significativa? Explique.

**Respuesta:** No. Una mejora del 1 % es más pequeña que la natural entre corridas (la
desviación estándar del fitness en nuestros experimentos es de ≈ 5–6 puntos porcentuales),
así que ni siquiera se puede afirmar con confianza que exista esa mejora. Y aun si
existiera, cuatro veces más memoria, ocho veces más tiempo de optimización y tres veces
más inferencia por 1 % es un mal negocio: el controlador de 5 términos domina esa
comparación.

## 24. ¿La solución de pyGAD es necesariamente un óptimo global?

> **Pregunta original:** 24. ¿La solución encontrada por pyGAD puede considerarse
> necesariamente un óptimo global? Explique utilizando los conceptos de exploración,
> explotación, óptimo local y óptimo global.

**Respuesta:** No. pyGAD *explora* (con mutación y cruce, probando zonas nuevas del
espacio) y *explota* (con selección y élite, afinando lo mejor encontrado); el balance
entre ambas decide qué tan lejos llega. El espacio es tan grande y con tantos valles
buenos que el algoritmo puede detenerse en un óptimo local, no en el global. Solo se
puede afirmar honestamente: "la mejor solución encontrada con este presupuesto, esta
configuración y estas semillas", y por eso se reportan las 5 corridas con promedio y
desviación.

## 25. ¿Por qué 5 ejecuciones con semillas distintas?

> **Pregunta original:** 25. ¿Por qué este examen exige realizar al menos 5 ejecuciones
> independientes utilizando semillas distintas? ¿Qué problema metodológico se intenta
> evitar?

**Respuesta:** Porque el algoritmo genético es azaroso: cada corrida puede dar un
resultado distinto. Con 5 semillas se obtiene el promedio y la desviación estándar de
cada métrica, lo que muestra el comportamiento *típico* del método y no la corrida
afortunada. El problema que se evita es el cherry-picking: reportar solo el mejor intento
como si fuera lo normal, cuando en realidad es la cola de la distribución.

## 26. Reportar solo la mejor corrida: por qué engaña

> **Pregunta original:** 26. Si un estudiante reporta únicamente la mejor corrida
> obtenida durante sus experimentos, ¿por qué sus conclusiones podrían ser engañosas?

**Respuesta:** Porque la "mejor corrida" es un resultado excepcional, no el habitual: con
5 intentos, puede quedar varias desviaciones estándar por encima del promedio. Las
conclusiones extraídas de ese valor ("el de 9 términos es el mejor") podrían cambiar por
completo si se hubiera elegido otra semilla, y además se esconde la varianza del método,
que es parte de su calidad. Es como juzgar a un atleta por su mejor marca única en vez
de por su desempeño consistente.

## 27. Distintas corridas, controladores distintos, fitness similares: ¿qué indica?

> **Pregunta original:** 27. Durante la optimización observó que distintas ejecuciones
> generan controladores completamente diferentes pero con fitness similares. ¿Qué indica
> esto acerca del espacio de búsqueda?

**Respuesta:** Que el espacio tiene muchísimas soluciones casi igual de buenas: es un
mapa multimodal, con muchas "cimas" de altura parecida en vez de una única cima. Esto es
natural en sistemas difusos porque las funciones se superponen: cambiar ligeramente
reglas vecinas puede dejar el desempeño casi intacto. La consecuencia práctica es doble:
la solución obtenida es *una* buena, no *la* buena; y conviene quedarse con la más
simple, apoyándose en las 5 semillas para confirmarlo.

## 28. ¿Existe un número óptimo de términos para este problema?

> **Pregunta original:** 28. ¿Considera que existe un número óptimo de términos
> lingüísticos para este problema? Argumente utilizando los resultados obtenidos.

**Respuesta:** Con los resultados obtenidos: existe una *zona* de mejor compromiso, no un
número óptimo absoluto. El fitness no mejoró de forma clara al subir de 5 a 9 términos,
mientras que los costos crecieron con seguridad (inferencia ×3.6, memoria ×2.9). El
equilibrio desempeño/costo apunta a los controladores de 5 o 7 términos; no vimos
evidencia de que 9 términos pague su precio. La respuesta definitiva se escribe con la
tabla final regenerada y su análisis estadístico, no como opinión.

## 29. Comparación final entre 5, 7 y 9 términos

> **Pregunta original:** 29. Con base en sus resultados experimentales: compare los
> controladores de 5, 7 y 9 términos; analice sus ventajas y desventajas; discuta el
> impacto del costo computacional; determine cuál representa el mejor equilibrio entre
> desempeño y complejidad. La respuesta deberá sustentarse mediante evidencia
> experimental.

**Respuesta:** Con la tabla de resultados: los tres logran un desempeño similar en
fitness (diferencias dentro del ruido estadístico), pero sus costos no son parecidos.
Ventajas y desventajas: 5 términos es el más rápido (≈ 10 ms de inferencia, ≈ 0.49 MB de
memoria) y el más simple; 9 términos ofrece el mapeo más fino, pero cuesta ≈ 37 ms,
≈ 1.44 MB y 243 genes, sin compensar con desempeño. El tiempo de optimización apenas
cambió (×1.07), así que el costo real se ve en la inferencia y la memoria. El mejor
equilibrio es el de 5 términos (o 7 si la campaña final muestra una ventaja real),
por igualar el desempeño con la menor complejidad.

## 30. Trade-off desempeño ↔ complejidad y decisión industrial

> **Pregunta original:** 30. Durante muchos años una gran parte de la investigación en
> inteligencia artificial y control se enfocó principalmente en maximizar el desempeño
> de los sistemas. Sin embargo, en aplicaciones reales también resultan importantes
> aspectos como complejidad computacional, tiempo de ejecución, consumo de memoria,
> facilidad de mantenimiento e interpretabilidad del modelo. Con base en los resultados
> obtenidos en este examen: (a) analice el compromiso (trade-off) entre desempeño y
> complejidad; (b) determine si incrementar el número de términos lingüísticos produjo
> una mejora real o únicamente una mayor complejidad; (c) argumente cuál de los tres
> controladores optimizados utilizaría en una aplicación industrial real; (d) justifique
> su respuesta utilizando exclusivamente evidencia experimental obtenida durante el
> examen.

**Respuesta:** (a) El desempeño se satura mientras la complejidad no deja de crecer: del
5 al 9 términos, inferencia ×3.6, memoria ×2.9, genes ×2.55 y un espacio de búsqueda
~10⁶¹ veces mayor, contra diferencias de fitness dentro del ruido. (b) En la práctica,
más términos produjo sobre todo *más complejidad*, no una mejora demostrable. (c) En una
aplicación industrial usaríamos el de 5 términos (o el de 7 si la campaña final confirma
una ventaja real), porque logra las mismas métricas exigidas con el menor costo
computacional y la base de reglas más fácil de entender y mantener. (d) Todo lo anterior
se apoya únicamente en los resultados del examen: tabla obligatoria de resultados,
promedio y desviación de las 5 corridas por configuración, y las curvas de convergencia;
ninguna parte responde "por intuición".

---

## Nota de trazabilidad

- Cifras citadas: campaña de la versión archivada (`codigo de cristian/results/`) usada
  como referencia provisional; se regeneran con `uv run python main.py --force`.
- Análisis complementarios que respaldan respuestas concretas: ablación regla por regla
  (P6, P29), prueba estadística Mann-Whitney (P1, P2, P23), cobertura de reglas
  (`rule_coverage` en los JSON, P6–P7) y justificaciones de diseño
  (`docs/PREGUNTAS_PROFESOR.md`, `docs/CORRECCIONES_PARCIAL2.md`).
