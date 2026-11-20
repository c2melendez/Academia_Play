# Catálogo canónico de gates v4.0

Los IDs **nombrados** sustituyen los números ambiguos G0–G12 de v2/v3. Un gate solo puede producir `DOC_PASS`, `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`, `PENDING_REVIEW`; los gates de diseño admiten `DOC_PASS` tras inspección real de documentos y validación estructural, no `PASS`. Los gates técnicos exigen `E1` y pruebas/logs asociados al insumo. `INCONCLUSIVE` es un resultado de oráculo, nunca estado de gate aprobado.

| ID | Requisito verificable | Naturaleza | Cierre |
|---|---|---|---|
| `G-SOURCE` | Ediciones, huellas, páginas inspeccionadas, permisos y trazabilidad de fuentes | Documental y originalidad | `DOC_PASS`; `SOURCE_MISSING` bloquea objetivos afectados |
| `G-CURRICULUM` | Cobertura de objetivos, dependencias, institución/curso/version y trazas hasta ítems | Documental/estructural | `DOC_PASS` con validación efectiva |
| `G-DESIGN` | 3 diseños por familia, uno no simulado, evidencia realmente abierta, selección, aprobación vigente | Humano + documental | `DOC_PASS` tras `APROBAR_DISEÑO` |
| `G-LAB` | Necesidad curricular y `REUSE/EXTEND/CREATE`, prueba de integración y accesibilidad | Técnico | `PASS` E1 cuando aplica; `NO_LAB` razonado |
| `G-ORACLE` | Casos dorados, negativos, inconclusos, dominio y unidades, aislamiento de ejecución | Técnico | `PASS` E1, nunca `INCONCLUSIVE` |
| `G-PEDAGOGY` | Operación cognitiva, variantes distintas, feedback por error, transferencia, límites de ayuda | Técnico/documental | `PASS` E1 para implementación |
| `G-PROGRESS` | Unión monotónica, idempotencia, concurrencia, migraciones y dominio separado | Técnico | `PASS` E1 |
| `G-A11Y` | WCAG 2.2 AA, axe + revisión teclado/lector, matemáticas accesibles y fallback | Técnico/manual | `PASS` con evidencia completa o `PENDING_REVIEW` |
| `G-SECURITY` | parser restringido, auth/privacidad, secretos, límites CPU/memoria, cadena dependencias | Técnico/legal | `PASS` E1 para lo comprobado |
| `G-REGRESSION` | unitarios, contratos, E2E, propiedades, rendimiento móvil y fixtures | Técnico | `PASS` E1 |
| `G-DEPLOY` | CI exitoso y despliegue verificado del mismo SHA de producción o staging autorizado | Técnico | `PASS` E1; `NOT_RUN` si no accesible |
| `G-ACADEMIC` | Firma docente, fuentes, criterios y revisión de contenido por versión | Humano | `PENDING_REVIEW` o aprobación humana registrada |
| `G-EMPIRICAL` | Protocolo ético, consentimiento, muestra, línea base, retención y transferencia | Humano/investigación | `PENDING_REVIEW` o evaluación documentada |

## Evidencia obligatoria para PASS

`gate_id`, `module_id`, `input_hash`, `acceptance_revision`, `evidence_level`, `commit_sha` (si existe Git), `commands`, `logs`, `observed_at`, `reviewer`, `limitations`, `result`; `workflow_run_id` y `deployment_sha` cuando aplique. No sustituir evidencia por un estado JSON escrito a mano. Un `PASS` sin `E1`, comandos y logs verificables es inválido. En entorno local sin Git remoto, una prueba realmente ejecutada puede acreditar gates locales (`E1`) con hash de checkout, pero **nunca `G-DEPLOY`**.

## Criterio de DONE_TECHNICAL

Requiere gates técnicos pertinentes `G-LAB` (o `NO_LAB` justificado), `G-ORACLE`, `G-PEDAGOGY`, `G-PROGRESS`, `G-A11Y`, `G-SECURITY`, `G-REGRESSION` y `G-DEPLOY` en PASS E1; gates documentales `G-SOURCE`,`G-CURRICULUM`,`G-DESIGN` en DOC_PASS. Si el proyecto carece de acceso a despliegue, usar `DONE_LOCAL` y `G-DEPLOY=NOT_RUN`, nunca `DONE_TECHNICAL`. `G-ACADEMIC` y `G-EMPIRICAL` se registran aparte y no bloquean trabajo técnico independiente.