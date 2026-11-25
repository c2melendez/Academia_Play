# Arquitectura pedagógica fundacional — Academia Play v4.2

## Producto, no documentación
La unidad educativa es una **competencia de curso universitario real**, con fundamentos necesarios y una experiencia donde el estudiante razona, actúa y transfiere. Un capítulo no equivale a un módulo; una pregunta de opción múltiple no equivale a una experiencia. La calidad técnica mantiene su valor instrumental.

## Modelo fundacional de cinco capas
1. **CURRICULAR_TARGET:** desempeño observable del sílabo, edición/versiones y páginas fuentes.
2. **FOUNDATION:** conocimiento anterior indispensable; origen rastreado o hipótesis pendiente; máximo alcance justificado por target.
3. **CONCEPTUAL_BRIDGE:** experiencia que conecta foundation con target, con predicción y representación distinta.
4. **INTERACTIVE_EXPERIENCE:** secuencia guiada y evidencia del razonamiento, incluida retroalimentación causal.
5. **TRANSFER_EVIDENCE:** tarea novedosa sin ayuda reveladora, independiente de la prueba formativa y del examen.

Metadatos mínimos por nodo: `id`, `kind`, `description`, `objective_id`, `source_refs`, `evidence_status` (`VERIFIED`/`PENDING_VALIDATION`/`SYNTHETIC`), `prerequisite_ids`, `diagnostic_prompt`, `remediation_activity_id`, `exit_criterion`. Son un **contrato de diseño v4.2**, no campos ya exigidos por los schemas v4.1. No modificar esos schemas a ciegas: migración y tests de compatibilidad se harán con el primer curso real aprobado.

El diagnóstico debe ser breve, explicativo y no punitivo; una sola respuesta no atribuye estado mental. Una brecha desencadena apoyo; el alumno puede acceder de modo voluntario al fundamento o retornar al curso. Mantener `unlocked_access` y `mastery_estimate` separados, como en v4.1.

## Contrato de una experiencia, por competencia
- **Antes:** objetivo, conocimientos previos, representación intuitiva, criterio verificable de éxito y carga cognitiva.
- **Explorar:** problema auténtico o predicción, manipulación significativa o razonamiento asistido, contraste de observaciones. Un gráfico solo aporta cuando la variación manipulada enseña una relación.
- **Explicar:** formalizar el concepto tras la exploración cuando resulte apropiado; ejemplos trabajados para novatos y retiro gradual de pistas.
- **Practicar:** familias semánticamente distintas, feedback que explique *por qué* una respuesta es errónea, no únicamente el resultado.
- **Transferir:** aplicar el concepto a datos, representaciones o contextos nuevos, sin filtrar la solución desde Ruta o Tutor al Examen.
- **Recordar:** recuperación posterior y práctica distribuida, adaptando a la dificultad y al progreso sin convertir XP/rachas en dominio.
- **Acceder:** teclado, lector de pantalla, alternativa verbal/tabular de gráficos, móvil y ancho de banda bajo.

No imponer la misma secuencia a todas las disciplinas: al comparar tres diseños didácticos debe existir al menos una alternativa no simulada; elegir según objetivo y evidencia.

## Modos con propósito claro
- **Ruta:** desbloqueo por dominio demostrado y acceso permanente; incorpora remediación de fundamentos y retorno rápido.
- **Tutor:** pistas graduadas y práctica voluntaria, explicaciones causalmente correctas; errores como hipótesis.
- **Laboratorios:** REUSE > EXTEND > CREATE y solo cuando la manipulación aporta.
- **Examen:** ítems independientes, sin ayudas durante evaluación y sin contaminar el conjunto de transferencia.

## Investigación: requisito verificable, no adorno
Para cada familia curricular registrar en `docs/EVIDENCE_REGISTER.md` DOI/URL efectivamente consultada, población, evidencia a favor/en contra, límites, magnitud del efecto si procede, técnica y decisión. Sin consulta, `NOT_VERIFIED`. Una revisión general STEM no justifica automáticamente la aplicación a programación, química o ingeniería, ni garantiza eficacia del diseño específico.

**Referencias base verificables para orientar búsqueda, no estudios de eficacia del proyecto:**
- Freeman et al. (2014), *PNAS*, 225 estudios STEM, DOI 10.1073/pnas.1319030111: https://pubmed.ncbi.nlm.nih.gov/24821756/
- Dunlosky et al. (2013), *Psychological Science in the Public Interest*, revisión de técnicas de estudio: https://pubmed.ncbi.nlm.nih.gov/26173288/
- National Academies (2018), *How People Learn II*, conocimientos previos, contexto y transferencia: https://www.nationalacademies.org/read/24783/chapter/2
- Theobald et al. (2020), *PNAS*, metaanálisis sobre aprendizaje activo y brechas: https://pubmed.ncbi.nlm.nih.gov/32152114/

Estos estudios respaldan familias de estrategias y son contextuales; no equivalen a evidencia empírica de Academia Play.

## Criterios pedagógicos de aceptación del primer corte
1. Identidad real: sílabo y edición + libro autorizado y páginas comprobadas.
2. Diseño aprobado para la revisión exacta, no inferido del permiso de infraestructura.
3. Al menos un target, un foundation y un conceptual bridge trazados; ruta recuperativa funcional.
4. Una interacción en navegador donde el alumno produce razonamiento observable, no solo lee un texto.
5. Retroalimentación causal, pistas graduadas y alternativa accesible.
6. Oráculo independiente con positivos/negativos/`INCONCLUSIVE`; no corregir el oráculo para lograr verde.
7. Práctica autónoma y transferencia nueva; evaluación de examen separada.
8. Progreso persistente, pruebas funcionales/E2E y gates aplicables. CI y despliegue mismo SHA si se publica.
9. Revisión docente y evaluación empírica con estados independientes, no supuestas.

## Medición y priorización
Los reportes separan PRODUCTO, CALIDAD EDUCATIVA y SALUD TÉCNICA. Una propuesta o fixture sintético no aumenta el contador de competencias reales implementadas. Un CI exitoso no aumenta el contador de estudiantes que dominan un fundamento. Prioridad operativa: insumos curriculares reales → investigación/diseño → primer corte → corrección → siguiente competencia. No ampliar gobernanza general si no reduce un riesgo específico del corte.

## Ausencia actual de curso
Mientras `continuity.json.course_design_status=SOURCE_MISSING`, es válido elaborar mapas y ejemplos **etiquetados sintéticos**, investigar técnicas y crear componentes genéricos fuera de M0 curricular; está prohibido presentarlos como cobertura de la UNAH u otra universidad. La siguiente dependencia curricular es el sílabo del primer curso y bibliografía con ediciones.
