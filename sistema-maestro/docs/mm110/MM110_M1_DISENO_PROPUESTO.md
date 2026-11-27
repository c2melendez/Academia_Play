# MM-110 — M1 Polinomios: propuesta de diseño r2

Estado: DESIGN_PROPOSED / E3; no constituye APROBAR_DISEÑO ni aprobación académica. Alcance propuesto univariado sobre Q, interpretación sobre R. No modifica la revisión F01 aprobada. Dependencia curricular: F01; soporte local SQLite. Supabase y Render dinámico diferidos hasta completar certificación pedagógica y funcional local de MM-110 por decisión del propietario.

## Procedencia y límites

Base documental: MM110_RECONSTRUCCION_CURRICULAR.json, afirmación C2 (S2/S3, acceso parcial histórico); MM110_SILABO_PROPUESTO.md, M1; MM110_MATRIZ_TRAZABILIDAD_BIBLIOGRAFICA.md (Larson 8, A.3 y 2.3 como referencias de índice, no páginas de ejercicios auditadas). Swokowski 13 p. 4 y Sullivan 11 pp. 10 y 16 fueron inspeccionados para F01, no acreditan todo M1. Cotejo de secciones, profundidad y vigencia pendiente. Los ejemplos de abajo son originales y constituyen propuestas pedagógicas, no atribuciones a fuentes. No afirmar cobertura oficial.

## Secuencia y aceptación por familia

| Familia | A: diagnóstico | B: puente visual y alternativa textual | C: competencia y variantes | T: transferencia inédita |
|---|---|---|---|---|
| F02 Estructura | Potencias enteras no negativas; identificar coeficiente | Tarjetas de términos y tabla exponente-coeficiente | Clasificar, reducir antes de determinar grado, distinguir polinomio cero de constante no nula | Inferir grado tras cancelación en un modelo |
| F03 Suma/resta | Signos y términos semejantes | Columnas por exponente con alternativa lineal | Sumas, resta con paréntesis, términos ausentes y cancelación | Diferencia de dos modelos polinómicos y justificación |
| F04 Multiplicación | Distributividad F01 y ley de exponentes | Cuadrícula de productos parciales, tabla accesible | Monomio por polinomio, binomios, polinomios con signos y fracciones | Modelo de área con lados polinómicos y restricciones físicas explícitas |
| F05 Productos notables | Multiplicar binomios | Descomposición de áreas positivas, tabla y derivación simbólica | Cuadrado, conjugados, cubo; reparación de fórmulas falsas | Seleccionar identidad para simplificar una expresión nueva |
| F06 Factorización | Factor común e inversión | Agrupar términos y construir rectángulos; alternativa algebraica | Factor común, agrupación, diferencia de cuadrados, trinomios sobre Q; distinguir equivalencia de forma factorizada | Recuperar dimensiones a partir de un área, cuando el contexto lo permita |
| F07 División | Operaciones F03/F04, divisor no nulo | Tabla de división larga y sintética con pasos escritos | Cociente y residuo, divisor lineal, teorema del residuo y factor | Reconstruir dividendo y detectar residuo incompatible |

## Alternativas, decisión propuesta

A: organizador manipulable con predicción, útil para conexión entre representaciones; riesgo de carga y metáforas inválidas con signos. B: clasificación y reparación de errores con justificación, económica y accesible; riesgo de acierto por descarte. C: ejemplo simbólico trabajado seguido de retiro de ayuda, sin simulación, útil para generalización; riesgo de copia. Combinar A breve y opcional con B/C, ofreciendo ruta simbólica completa. No inferir eficacia sin estudio. No crear simulador redundante.

## Oráculo y aceptación

REUSE del normalizador racional exacto F01, previa inspección de límites; EXTEND de validación de forma para polinomio reducido, grado y factorización. No usar igualdad por muestreo. Grado del cero: no definido en este diseño; caso explícito. Para F06 verificar identidad exacta y forma exigida; no afirmar factorización irreducible sin prueba de irreducibilidad sobre el dominio. Para F07 comprobar D=d*q+r, d no nulo y r=0 o grado(r)<grado(d); división sintética ordinaria solo con divisor x-a. No cambiar la política de dominio F01. Casos positivos, negativos, cancelaciones, dominio inválido y agotamiento computacional INCONCLUSIVE; fixtures independientes del generador.

Ejemplos originales: F02 4x^3-4x^3+2x-1 tiene grado 1; F03 (3x^2-2x+1)-(x^2+4x-5)=2x^2-6x+6; F04 (2x-3)(x+4)=2x^2+5x-12; F05 (x-5)^2=x^2-10x+25; F06 x^2-7x+12=(x-3)(x-4); F07 x^2+1 dividido entre x-1 da cociente x+1, residuo 2. Cada uno requiere una justificación distinta de repetir el resultado.

## Evaluación y controles

Bancos formativo, transferencia y examen separados, variantes semánticas nuevas; ayuda reveladora excluye evidencia autónoma. Dominio propuesto por familia: dos operaciones de razonamiento distintas y transferencia inédita sin ayuda, pendiente de aprobación y revisión del contrato. No equiparar número de aciertos con dominio. Errores: combinar exponentes al sumar, no distribuir signo negativo, omitir producto cruzado, confundir cuadrado de suma, declarar factorización sin forma, ignorar grado del residuo. Retroalimentación causal y remediación específica. Examen acumulativo con revisión diferida y prevención de consulta de soluciones, reutilizar F01 con adaptación por familia. Accesibilidad: teclado, zoom, texto equivalente a gráficas y tablas, axe y revisión humana. Pruebas de regresión y persistencia local; revisión docente y empírica independientes.

## Próximo gate

Cotejar fuentes y alcance para F02–F07; revisar alternativas y reglas de aceptación; obtener APROBAR_DISEÑO sobre revisión exacta antes de incorporar M1 al manifiesto aprobado o implementar currículo real. Mantener M0 IN_PROGRESS hasta reconciliar controles locales y revisiones aplicables. Las tareas de investigación y diseño pueden avanzar en paralelo sin declarar certificación.

## Cobertura detallada y criterios adicionales r2

- F02: distinguir expresión polinómica de expresión racional no polinómica; grado después de reducción; cero sin grado definido.
- F03: sumar/restar por coeficientes, conservar términos ausentes y comprobar cancelaciones.
- F04: productos de monomios y polinomios, signos y coeficientes racionales; reducción de productos parciales.
- F05: cuadrados y cubos de binomios y producto de conjugados; distinguir fórmulas falsas mediante expansión exacta.
- F06: factor común, agrupación, diferencia de cuadrados, trinomio cuadrado perfecto, trinomios con coeficiente principal no unitario y suma/diferencia de cubos. Exigir forma y equivalencia; no confundir factorización parcial con irreducibilidad.
- F07: división larga con divisores lineales y de grado superior, división sintética para x-a, residuo y factor; verificar identidad y grado del residuo, incluido residuo cero. No admitir divisor cero.

Los ajustes son propuestas de cobertura matemática; falta cotejo de libros originales y confirmación del alcance institucional. Referencias complementarias a comprobar: OpenStax Algebra and Trigonometry 2e, secciones 1.4, 1.5, 5.4 y 5.5. No afirmar inspección nueva de estas páginas ni aprobación institucional.

## Reutilización técnica comprobada por inspección

El módulo mm110_f01_oracle.py normaliza polinomios univariados sobre Q con límites de 256 caracteres, 128 tokens, grado 16, 256 bits por numerador/denominador y profundidad 24. Reutilizar normalize, add, mul y Verdict; no ampliar límites por defecto. Las pruebas técnicas de componentes genéricos no son implementación curricular aprobada. Mantener aislamiento de proceso antes de exponer nuevos oráculos a entradas estudiantiles. La revisión F01 y su hash permanecen intactos.
