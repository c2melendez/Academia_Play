# GATES — Academia Play v4.1

**Fuente única del catálogo de gates.** La estructura y los enumerados de los registros están en `schemas/gate.schema.json`. Los identificadores antiguos G0–G12 no son válidos; `G-A11Y` queda como alias histórico que no satisface los dos nuevos controles.

## Estados de un gate

- `DOC_PASS`: documentación inspeccionada y contrato validado; solo gates `G-SOURCE`, `G-CURRICULUM`, `G-DESIGN`. No implica software ejecutado.
- `PASS`: **E1**, pruebas/comandos realmente ejecutados sobre la versión objeto de la verificación, con logs/artefactos rastreables. Una declaración JSON no es prueba.
- `FAIL`: evidencia de defecto verificado.
- `BLOCKED`: dependencia, autorización, fuente o entorno impide terminar.
- `NOT_RUN`: prueba no ejecutada. Nunca es `PASS`.
- `PENDING_REVIEW`: falta firma o evaluación humana.
- `NOT_APPLICABLE`: permitido únicamente para `G-LAB` cuando no procede laboratorio, o `G-A11Y-MANUAL` para cambios **sin interfaz ni contenido de estudiante**, siempre con razón escrita y revisión de alcance. No confundir con no haber ejecutado una prueba.

Los tres niveles de evidencia permanecen: `E1` es salida real verificable, `E2` código escrito/no ejecutado, `E3` diseño. El oráculo usa `VERIFIED/REJECTED/INCONCLUSIVE`; no son estados de gate.

## Catálogo y criterios de cierre

| Gate | Evidencia y alcance necesario | Política de cierre |
|---|---|---|
| `G-SOURCE` | Sílabo real, edición, licencia, hash y páginas realmente examinadas; derechos y originalidad | `DOC_PASS` o `BLOCKED` por `SOURCE_MISSING` |
| `G-CURRICULUM` | Competencias, prerrequisitos, curso/versión, cobertura de fuentes y actividades; validación estructural | `DOC_PASS` |
| `G-DESIGN` | 3 alternativas didácticas por familia, una sin simulación; aprobación humana asociada a hash de diseño | `DOC_PASS` tras `APROBAR_DISEÑO` |
| `G-LAB` | Motivación pedagógica, REUSE/EXTEND/CREATE, ADR, tests de escenario, oráculo y alternativa accesible | `PASS` E1 o `NOT_APPLICABLE` justificado |
| `G-ORACLE` | Ejecutar fixtures positivos, negativos, casos límite y `INCONCLUSIVE`; tolerancia, dominio, unidades y límites de cómputo | `PASS` E1; `INCONCLUSIVE` de una respuesta estudiantil no es un pase |
| `G-PEDAGOGY` | Variantes semánticas, retroalimentación causal, ayudas graduadas, transferencia formativa independiente del examen | `PASS` E1 por implementación, revisión docente aparte |
| `G-PROGRESS` | Dominio derivado de evidencias y política aprobada, uniones conmutativas/asociativas/idempotentes, grants permanentes, migraciones | `PASS` E1 |
| `G-A11Y-AUTO` | axe/Lighthouse o equivalente con logs, estructura semántica y contraste; pruebas teclado automatizables | `PASS` E1 para alcance automatizado, no certifica WCAG por sí solo |
| `G-A11Y-MANUAL` | Recorrido real de teclado, lector de pantalla, zoom, gráficas con alternativas, criterio WCAG 2.2 AA | `PASS` con revisor/evidencia humana; `PENDING_REVIEW` si falta; `NOT_APPLICABLE` solo cuando no hay UI |
| `G-SECURITY` | Modelo de amenazas, secretos, auth, permisos, protección de datos, entrada restringida, dependencia y sandbox cuando aplica | `PASS` E1 para alcance declarado; ninguna vulnerabilidad crítica abierta |
| `G-REGRESSION` | Unitarias, negativas con códigos de error, propiedad/integración/E2E pertinentes, rendimiento en móvil | `PASS` E1 |
| `G-DEPLOY` | CI verificado, commit SHA y deployment SHA idénticos para staging/producción, smoke comprobado | `PASS` E1 del mismo SHA; `NOT_RUN` si no desplegado |
| `G-ACADEMIC` | Objetivos/fuentes, ítems, retroalimentación, oráculos y firma de revisor docente autorizada | `PENDING_REVIEW` hasta registro humano; no auto-PASS |
| `G-EMPIRICAL` | Consentimiento/ética cuando aplique, protocolo, retención, transferencia y resultados | `PENDING_REVIEW` hasta estudio realizado y evaluado |

## Perfil mínimo por hito

- **Bootstrap técnico:** identidad GitHub y Render observada, accesos verificados, contratos de infraestructura. No constituye M0 ni exige un sílabo.
- **M0 / primer curso propuesto:** `G-SOURCE`, `G-CURRICULUM`, `G-DESIGN` documentales; `SOURCE_MISSING` bloquea `G-CURRICULUM` y `G-DESIGN` curriculares reales.
- **`DONE_LOCAL`:** módulo construido y pruebas locales aplicables ejecutadas. Los gates no ejecutados se mantienen `NOT_RUN` y la implementación no se presenta como publicada.
- **`DONE_TECHNICAL`:** gates documentales aplicables `DOC_PASS`, técnicos aplicables `PASS` E1 (incluyendo `G-DEPLOY`), `G-LAB` y `G-A11Y-MANUAL` opcionalmente `NOT_APPLICABLE` justificados. Para un módulo con UI estudiantil, la revisión manual de accesibilidad debe terminar antes de declarar `DONE_TECHNICAL`. No confundir despliegue provisional con producto certificado.
- **Aprobación académica/empírica:** flujos humanos independientes; pueden permanecer pendientes mientras se desarrollan módulos técnicos sin anunciar certificación.

Los gates se escogen por **impacto técnico y educativo** (análisis de diferencias); un cambio editorial no fuerza rehacer oráculos intactos, pero sí debe verificar validez textual y ausencia de regresiones pertinentes.

## Evidencia y controles de honestidad

El gate debe declarar `gate_id, module_id, input_hash, acceptance_revision, evidence_level, commands, logs, observed_at, reviewer, limitations, result` y SHA/CI/deployment cuando aplique. `input_hash` y `acceptance_revision` identifican exactamente la implementación bajo revisión. Nunca rellenar logs, fechas, SHA ni firma docente ficticios para lograr verde.

Las pruebas de accesibilidad automatizadas no demuestran WCAG completa. Un gate `PASS` **no** puede esconder en `limitations` auth, sandbox, secretos, o pruebas imprescindibles no realizadas. Esas ausencias producen `BLOCKED`/`NOT_RUN` o un gate separado; no `PASS` parcial.

## Criterios de procedencia curricular v4.3

`G-SOURCE` distingue fuente institucional confirmada, reconstrucción documental e inferencia; una propuesta `RECONSTRUCTED_PROPOSED` **no** adquiere `DOC_PASS` como sílabo oficial por sí sola. La validación estructural del expediente `reconstructed_curriculum.schema.json` y su validador no demuestran autenticidad, exhaustividad ni independencia reales de los documentos. Un programa adoptado por decisión humana explícita puede habilitar el **diseño para la plataforma** bajo alcance y limitaciones declarados; no se certifica la cobertura oficial de la universidad si no existe evidencia institucional suficiente.

`G-CURRICULUM` debe conservar la matriz de afirmaciones/fuentes, discrepancias, fundamentos y profundidad; `G-DESIGN` sigue exigiendo `APROBAR_DISEÑO` con revisión exacta. Los gates técnicos/empíricos existentes no se modifican; la investigación preliminar puede avanzar con `SOURCE_MISSING` sin convertirlo en `PASS`. Los manifiestos de cursos reconstruidos requieren migración explícita del contrato `syllabus_source_id`, sin crear fuentes oficiales ficticias.
