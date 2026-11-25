# EVIDENCE REGISTER — Academia Play v4.2

**Estado:** bibliografía general de partida, **no** registro de eficacia de un curso de Academia Play. Toda nueva ficha requiere apertura/lectura real de la fuente por el ejecutor y trazabilidad al objetivo concreto. Usar `NOT_VERIFIED` si no se ha consultado; `COURSE_PENDING` si falta sílabo. No inventar tamaños muestrales, resultados ni significación.

## Plantilla de ficha por decisión didáctica
- `study_id` / `course_id` / `objective_id` / `discipline` / `audience`
- `title`, `authors`, `year`, `doi_or_url`, `accessed_at`
- `evidence_type`: estudio primario / revisión sistemática / metaanálisis / teoría / experiencia local
- `context`, `sample`, `comparison`, `outcomes`, `effect_and_uncertainty` (si están disponibles)
- `supporting_findings`, `contrary_findings`, `heterogeneity`, `limitations`
- `confidence`: alta / moderada / baja / insuficiente, **justificada**, no etiqueta automática
- `design_decision`, `rejected_alternative`, `hypothesis`, `falsification_test`, `transfer_measure`
- `verification_status`: `SOURCE_OPENED` / `NOT_VERIFIED`; `curricular_status`: `COURSE_PENDING` / `LINKED_TO_REAL_COURSE`

## Fuentes generales iniciales consultadas para orientar diseño
Estas fichas únicamente fundamentan decisiones generales; aún no se ha inspeccionado la bibliografía de una asignatura universitaria real.

### ER-001 — Aprendizaje activo en educación superior STEM
- Freeman et al. (2014), *Active learning increases student performance in science, engineering, and mathematics*, PNAS. https://pubmed.ncbi.nlm.nih.gov/24821756/
- Tipo: metaanálisis; 225 estudios; docencia universitaria STEM; comparó enseñanza tradicional y aprendizaje activo.
- Hallazgo general: mejora promedio de resultados académicos en condiciones de aprendizaje activo; diversidad de intervenciones y contextos, no receta universal.
- Limitación: no prueba la eficacia de un juego, laboratorio o interfaz particular de Academia Play.
- Decisión de diseño: preferir operaciones cognitivas activas a lectura pasiva; evaluar por comprensión y transferencia. Alternativa válida: explicación guiada activa sin simulación.
- Estatus: `SOURCE_OPENED` (registro bibliográfico/abstract); `COURSE_PENDING`.

### ER-002 — Recuperación y práctica distribuida
- Dunlosky et al. (2013), *Improving Students' Learning With Effective Learning Techniques*, Psychological Science in the Public Interest. https://pubmed.ncbi.nlm.nih.gov/26173288/
- Tipo: revisión de diez técnicas de estudio, general a múltiples edades y materiales.
- Hallazgo general: prácticas de recuperación y distribución temporal destacan por utilidad; condiciones específicas modifican efectos.
- Decisión: usar recuperación espaciada y contraste de variantes, sin confundir aciertos repetidos con dominio. Falta selección específica por asignatura.
- Estatus: `SOURCE_OPENED` (registro bibliográfico/resumen); `COURSE_PENDING`.

### ER-003 — Conocimientos previos y transferencia
- National Academies (2018), *How People Learn II: Learners, Contexts, and Cultures*. https://www.nationalacademies.org/read/24783/chapter/2
- Tipo: síntesis académica; los conocimientos previos y el contexto influyen sobre las estrategias que funcionan y la transferencia.
- Decisión: mapear fundamentos, diagnosticar sin estigmatizar, conectar representaciones y evaluar transferencia.
- Limitación: no prescribe una estructura universal ni un umbral de dominio para cada estudiante.
- Estatus: `SOURCE_OPENED` (síntesis accesible); `COURSE_PENDING`.

### ER-004 — Calidad y equidad del aprendizaje activo
- Theobald et al. (2020), *Active learning narrows achievement gaps for underrepresented students in undergraduate STEM*, PNAS. https://pubmed.ncbi.nlm.nih.gov/32152114/
- Tipo: metaanálisis de educación superior STEM con resultados de equidad reportados.
- Decisión: diseñar ayudas adaptativas, accesibilidad y tareas participativas; evitar recompensas que penalicen ritmos distintos.
- Limitación: no generalizar efectos por subgrupo o institución sin datos pertinentes, ni afirmar que el producto ya reduce brechas.
- Estatus: `SOURCE_OPENED` (registro bibliográfico/abstract); `COURSE_PENDING`.

## Pendientes obligatorios por disciplina
Para cada primera asignatura de matemáticas, física, química, ingeniería o programación: búsqueda acotada al contenido, resultados contrastantes, contexto, fuentes primarias y evidencia de métodos alternativos; documentación de hipótesis y criterios de evaluación. No replicar sin crítica el mismo diseño entre disciplinas.

## MM-110 / F01 — evidencia disciplinar y límites (2026-11-25)

### ER-MM110-01 — Strozier (2012)
- Fuente: https://holocron.lib.auburn.edu/handle/10415/3280 ; resumen institucional abierto, tesis íntegra no inspeccionada. `SOURCE_OPENED` (abstract), currículo reconstruido pendiente de adopción.
- Población: secundaria media con dificultades matemáticas; tamaño muestral no verificado. Estudio primario, diseño de sondeos múltiples entre conductas, intervención combinada concreto-representacional-abstracta (CRA) y mnemotecnia SUMLOWS para ecuaciones de uno, dos y varios pasos con distributividad.
- El resumen informa una relación funcional entre intervención y resolución de ecuaciones. No permite separar el aporte CRA del mnemónico, ni extrapolar magnitud o retención a universitarios. Confianza baja para MM-110, pertinente como hipótesis de diseño.
- Decisión: puente visual opcional y explícitamente limitado a áreas positivas, seguido de símbolos; alternativa completa sin simulación. Comparar con explicación simbólica sola, misma práctica y tiempo; tarea nueva con signos negativos, justificación y medición de ayudas. Refutar si no mejora comprensión/transferencia o aumenta errores de signo. No afirmar eficacia local.

### ER-MM110-02 — comparación de estrategias algebraicas
- Rittle-Johnson y Star (2007), https://eric.ed.gov/?id=EJ772031 ; y trabajo de 2009, https://ies.ed.gov/ncee/wwc/study/79862 . Extractos de búsqueda recuperados, apertura directa agotó tiempo: `NOT_VERIFIED` para texto completo y resultados; no citar tamaños de efecto ni usar como evidencia definitiva. El extracto de 2007 describe 70 alumnos de séptimo grado asignados a comparar métodos o estudiarlos secuencialmente.
- Hipótesis provisional, no inferencia causal local: contrastar expansión correcta con omisión de un término, pedir justificación y retirar ayudas; comparar con ejemplos sucesivos. Medir transferencia simbólica, no reconocimiento de respuesta. Evidencia contraria, magnitudes y heterogeneidad pendientes de inspección. F01 conserva ruta simbólica independiente como alternativa.
