# Diseño preliminar MM-110 r1 — DESIGN_DRAFT / E3

- M0 Fundamentos: áreas manipulables / clasificar equivalencias / ejemplo guiado (sin simulación).
- M1 Polinomios: mosaicos / construir factores / factorización escrita (sin simulación).
- M2 Expresiones racionales y radicales: dominio visual / detectar cancelación inválida / simplificación justificada (sin simulación).
- M3 Ecuaciones: balanza / desafío de incógnitas / resolución escrita (sin simulación).
- M4 Inecuaciones: recta interactiva / clasificar intervalos / tabla de signos (sin simulación).
- M5 Plano cartesiano: plano manipulable / ubicar puntos / problemas escritos (sin simulación).
- M6 Funciones: explorador gráfico / clasificar relaciones / tablas y fórmulas (sin simulación).
- M7 Funciones polinómicas y racionales: variar coeficientes / detectar ceros / análisis simbólico (sin simulación).
- M8 Composición e inversas: máquinas de funciones / ordenar composiciones / cálculo escrito (sin simulación).
- M9 Exponenciales y logaritmos: crecimiento interactivo / comparar modelos / problemas contextualizados (sin simulación).

M0 F01: diagnóstico, predicción, área positiva, distributividad formal, signos negativos, ayudas decrecientes, transferencia inversa y repaso. Oráculo independiente por coeficientes exactos sobre polinomios reales; entrada inválida REJECTED, fallo de cómputo INCONCLUSIVE. No usar muestreo como prueba de identidad. Ruta, Tutor y Examen con ítems separados. Acceso permanente y dominio variable; teclado y alternativa textual. Hipótesis: puente visual más práctica simbólica mejora transferencia; evaluar frente a ejemplo guiado. Evidencia disciplinar, comparación detallada, registry, pruebas y revisión exacta pendientes. No implementar M0 antes de APROBAR_DISEÑO y migración contractual.

## Especificación F01 r2 — borrador E3

Target curricular: transformar expresiones polinómicas mediante propiedades de los reales (M1/C2); M0 F01 es el apoyo habilitante, no un resultado oficial independiente. Fuentes: Swokowski 13 p. 4 y Sullivan Algebra & Trigonometry 11 pp. 10,16; ver matriz. Dominio: polinomios en x con coeficientes racionales exactos, evaluados sobre R; sin divisiones por expresiones variables, funciones ni exponentes no enteros en este corte.

### Alternativas F01
| Diseño | Beneficio esperado | Riesgo/carga | Accesibilidad/costo | Decisión |
|---|---|---|---|---|
| A área positiva con predicción | conecta producto con suma de áreas | no representa negativos literalmente | tabla y texto equivalentes; SVG sencillo | puente breve opcional |
| B detectar y reparar equivalencias | exige explicar términos omitidos y signos | selección por descarte | teclado; costo bajo | práctica autónoma con justificación |
| C ejemplo simbólico trabajado y retiro de ayudas | generaliza a signos y fracciones | copia mecánica si ayudas permanentes | texto matemático accesible; costo bajo | ruta principal después de A, alternativa completa sin simulación |

Hipótesis pendiente: A+C frente a C solo mejora transferencia a expresiones nuevas sin aumentar errores de signos; comparar aciertos sin ayuda y tiempo, no XP. No se afirma eficacia empírica. Registro científico disciplinar pendiente.

### Secuencia y ejemplos originales
1. Diagnóstico: comparar 4(2+5) con 4*2+5 y explicar; hipótesis de omisión si elige igualdad, no diagnóstico definitivo.
2. Predicción antes de mostrar áreas: rectángulo de altura 3 y ancho x+4, x>0; identificar dos productos. Alternativa textual: tres grupos, cada uno con x+4 elementos simbólicos.
3. Formalización: a(b+c)=ab+ac para reales; explicar que el modelo de áreas solo cubre magnitudes positivas. Ejemplo simbólico -3(2x-5)=-6x+15; pistas por signo y término.
4. Familia A: expandir 7(2x-3) a 14x-21 sin pistas reveladoras. Familia B: detectar y reparar la falsa identidad 5(x-4)=5x-4, justificando término constante -20. Transferencia independiente: una cuota de 8 por cada una de x unidades más 8 por cada una de 6 unidades; representar total como producto y suma, justificar equivalencia. Examen: banco separado, por ejemplo expansión con factor racional y verificación de una identidad diferente. No reutilizar ítems de transferencia.
5. Remediación: omisión → marcar cada término; signo → multiplicación de números con signo; confusión identidad/ejemplo → contraejemplo y normalización. Pistas graduadas: señalar, regla, ejemplo distinto, solución; última marca assisted=true. Repaso voluntario y recuperación posterior.

### Oráculo y aceptación previstos
Normalizar AST permitido a mapa exponente→coeficiente racional exacto; comparar mapas sin ceros. Gramática cerrada, límites de longitud, profundidad, grado y magnitud; sin eval. VERIFIED si igualdad exacta, REJECTED si desigualdad demostrada o entrada fuera de gramática (distinguir motivo, no penalizar error de formato como brecha conceptual), INCONCLUSIVE ante agotamiento o fallo interno; no otorgar dominio ni restar puntos. Positivos: 7(2x-3) vs 14x-21; negativos: 5(x-4) vs 5x-4; identidad falsa que coincide en un punto: x² vs x; caso de límite de cómputo simulado por inyección de fallo. Oráculo independiente del generador. Justificación conceptual evaluada por rúbrica explícita, no solo igualdad de coeficientes.

Dominio provisional: dos familias distintas y transferencia sin ayuda, con evidencia VERIFIED y justificación suficiente. Acceso desbloqueado monotónico; dominio revisable; eventos idempotentes; no datos personales en repo. Ruta/Tutor/Lab/Examen comparten objetivo y oráculo, no ítems. Teclado, lector de pantalla, alternativa tabular y textual, diseño móvil; pruebas E2E, persistencia y revisión humana pendientes. No se inicia implementación curricular. Registry y decisión REUSE/EXTEND/CREATE pendientes de inspección.

## Revisión r3 — propuesta delimitada para decisión humana

Estado de esta propuesta: DESIGN_PROPOSED para adopción provisional del núcleo reconstruido y autorización exclusiva del primer corte F01, sujeto a migración contractual antes de implementar. No acredita cobertura total ni oficialidad. M1–M9 son planificación preliminar; su desarrollo exigirá revisión de profundidad, fuentes y diseños por familia. Sistemas, complejos, vigencia institucional y ediciones no cotejadas permanecen abiertos. Fuentes curriculares: expediente MM110_RECONSTRUCCION_CURRICULAR.json blob 3a9e0ec86032e2408cc1c7e162f6c5b9fae0876c; referencias F01 en matriz bibliográfica. Evidencia ER-MM110-01: apoyo indirecto y limitado; ER-MM110-02 provisional, no verificada íntegramente. La ruta simbólica es alternativa completa al modelo de área; no se presume eficacia.

Grafo F01: F01-A (operaciones con signos y fracciones; diagnóstico de producto de dos racionales; remediación con recta y reglas; salida dos productos justificados) → F01-B (puente entre agrupación y distribución; predicción y explicación de dos productos; remediación con agrupación explícita) → F01-C (target M1/C2, expansión y factorización inversa; dos familias de evidencia sin ayuda reveladora) → F01-T (transferencia novedosa; construir y justificar expresiones equivalentes sin pistas). Evidencia de diseño E3; ninguna actividad implementada. Rúbrica: multiplicar cada término, conservar signos, justificar equivalencia general; no basta acertar por sustitución particular. Examen independiente. Las ayudas que revelan la regla o el procedimiento se registran como asistidas y no acreditan dominio autónomo. Los errores de formato no descuentan dominio; INCONCLUSIVE tampoco.

Decisión de arquitectura: REUSE/EXTEND preferentes; inventario real pendiente, no autoriza crear motor redundante. Si no existe componente compatible, documentar comparación y ADR antes de CREATE. No se autoriza costo, cambio de proveedor, datos personales ni despliegue de producto. Revisión docente y empírica independientes. La adopción humana de esta revisión no equivale a aprobación de todos los módulos, ni a autorización para modificar el alcance o el oráculo.

Canonicalización de esta revisión: UTF-8, Unicode NFC, finales LF, exactamente un LF final; SHA-256 sobre el documento completo, sin insertar el hash dentro de él. Registro de hash separado. Los cambios sustanciales invalidan la aprobación.
