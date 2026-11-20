# RUNBOOK — Academia Play v4.0

## Fuente de verdad y permisos

El repositorio canónico y HEAD real son autoridad técnica. En el paquete de trabajo, `schemas/*.schema.json` determinan las formas, `examples/manifest.json` ilustra el contrato, `continuity.json` si existe contiene estado técnico y `docs/` documenta decisiones. El reporte `STATE.md` se **genera**, no se mantiene de manera contradictoria con JSON. Los registros de gates se guardan como JSON con evidencia real; `EXECUTION_LOG.jsonl` es append-only.

| Acción | Autonomía |
|---|---|
| Diseñar, editar archivos locales, crear pruebas, ejecutar validadores | Sí |
| Commit/push a rama de trabajo **ya autorizada** | Sí, si los permisos y protecciones lo permiten |
| Crear repositorio público/privado, activar Render/Supabase y pagos | Autorización específica por proyecto y costo |
| Cambiar secretos, seguridad, producción, proveedor, borrar datos | Autorización específica y plan de reversión |
| Aprobar diseño y certificación académica | Usuario/revisor humano habilitado, no el agente |

`ENVIRONMENT_CONSTRAINED`: entorno sin capacidad de realizar/observar acciones externas; avanzar localmente y marcar `NOT_RUN` lo no ejecutado. `PROVISIONING_BLOCKED`: falta permiso o capacidad para crear recursos. No son excusa para declarar completado un gate no ejecutado.

## Máquina de estados

- Diseño: `DESIGN_DRAFT` -> `DESIGN_PROPOSED` -> `DESIGN_APPROVED` (requiere `APROBAR_DISEÑO` para la `design_revision` exacta); cambios sustanciales regresan a `DESIGN_PROPOSED`.
- Implementación: `PLANNED` -> `IN_PROGRESS` -> `DONE_LOCAL` -> `DONE_TECHNICAL` / `BLOCKED`. `DONE_LOCAL` no es despliegue; `DONE_TECHNICAL` exige gates definidos en GATES.md.
- Académico: `PENDING_ACADEMIC_REVIEW` -> `ACADEMICALLY_APPROVED` solo mediante firma docente comprobable; estado independiente del técnico.
- Empírico: `NOT_EVALUATED` -> `EMPIRICALLY_EVALUATED` con protocolo y datos auditables; distinto de aprobación docente.
- Evidencia: `E1`, `E2`, `E3`. Gate: `DOC_PASS`, `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`, `PENDING_REVIEW`.
- Estudiante: derecho de acceso (`LOCKED`/`AVAILABLE`) **monotónico**; estimación (`UNASSESSED`/`DEVELOPING`/`MASTERED`/`NEEDS_REVIEW`) variable y separada. No convertir una caída de dominio en cierre de acceso.

## Contrato de comandos

| Comando | Entrada | Efecto permitido | Salida/condición de parada |
|---|---|---|---|
| `INICIAR` | Insumos, permisos y estado | Diagnóstico, ingesta, 3 diseños por familia, propuesta de producto; NO M0 sin aprobación | `DESIGN_PROPOSED`; lista de fuentes ausentes; propuesta para aprobación |
| `APROBAR_DISEÑO` | ID/revisión exacta de propuesta y acto explícito del usuario | Registrar decisión; permite M0, **no** crea por sí solo recursos externos | `DESIGN_APPROVED`, aprobación fechada y ligada a revisión |
| `CONTINUAR` | Estado canónico, HEAD, autorización previa | Reparar gate rojo diferente o ejecutar módulo habilitado, pruebas y persistencia | Cierre completo o bloqueo específico; siguiente acción |
| `AGREGAR_CURSO` | Sílabo/ediciones/identidad institucional | Crear manifiesto versionado, comparar laboratorios, planear contenido; sin reprovisionar | Propuesta curricular y nuevos módulos |
| `AUDITAR` | Alcance/versión | Ejecutar validadores y pruebas sin cambiar código producto; puede escribir evidencia | Informe PASS/FAIL/NOT_RUN y diffs, sin certificación inventada |
| `RECONCILIAR` | Git/CI/Render/Supabase y continuidad | Actualizar observaciones y corregir referencias de estado, sin reescribir historia | Diferencias, siguiente acción, locks |
| `REPLANIFICAR` | Cambios de sílabo/libros/oráculos | Versionar impacto, plan de migración, preservar progreso | Manifiesto propuesto + nuevos gates |
| `ESTADO` | Registros canónicos | Solo lectura, generar resumen derivado | Estado, pruebas realmente observadas, riesgos |
| `VALIDAR_LABORATORIOS` | Registry, manifiesto | Solo validación de pertinencia/identidad/capacidades | Evidencias por laboratorio, bloqueos y decisiones |

## Primera corrida: diseño, luego infraestructura

1. Recibir sílabo oficial, libros de edición determinada y derechos de uso; calcular huellas y citar páginas realmente inspeccionadas; distinguir `SOURCE_MISSING` de contenido sustentado.
2. Construir grafo de objetivos/prerrequisitos con referencias a capítulos; investigar fuentes científicas abiertas y sus límites, explorar al menos 3 diseños por familia (uno no simulado); registrar `DETERMINADO`, `DEDUCIBLE`, `AMBIGUO`.
3. Aprobar diseño **antes** de M0 (regla de v2 restaurada). Presentar propuesta/ADR de infraestructura y solicitar permisos propios (repo público, proveedores, presupuesto y privacidad). Elige Render, Supabase o ambos según necesidad; no habilitar pagos implícitos.
4. Con autorizaciones comprobadas, crear **una sola vez** repo `academia-play`, rama canónica, CI, staging y datos mínimos. En nuevas sesiones verificar IDs existentes antes de aprovisionar; evitar duplicación.
5. Primer M0: rebanada vertical de un objetivo real. Implementar actividad original y dos familias distintas más transferencia, oráculo y caso INCONCLUSIVE, feedback diagnóstico, persistencia de acceso, pruebas negativas/E2E y un laboratorio solo si aporta al objetivo; demostrar proyecciones en ruta/tutor/examen y laboratorio o `NO_LAB`.
6. Auditoría separada del generador de contenido: scripts/oráculos independientes y revisión de QA; tratar disputas entre motores como INCONCLUSIVE. CI/deploy mismo SHA y docencia/empirismo por separado.

## Selección, tiempo y continuidad

- Reusar CI solo con igual hash de insumos, SHA y aceptación; ante corrida idéntica en curso esperar, ante fallo idéntico sin cambios diagnosticar y continuar con trabajo independiente; no relanzar en bucle.
- No imponer límites artificiales que fragmenten trabajo masivo; una corrida puede integrar trabajo coherente, pero bloqueos irreversibles y permisos sí detienen el tramo afectado.
- Nunca cancelar trabajos válidos ni fingir funcionamiento asíncrono. Ante interrupción registrar `continuity.json`, último cambio verificable, acciones realizadas y única acción siguiente.
- Revisión docente y piloto no deben impedir módulos técnicos independientes, pero sí la etiqueta pública correspondiente.

## Límite de dominio y evaluación

La política inicial configurable puede requerir dos variantes cognitivas distintas sin ayuda reveladora más un ítem de transferencia, con evidencia `VERIFIED`. No es un criterio universal validado; se calibra por curso, riesgo y datos. Pistas reveladoras marcan intento `assisted=true`; el simulacro bloquea pistas hasta el final. Una respuesta `INCONCLUSIVE` no resta puntos ni concede dominio. Variantes no se reducen a cambiar constantes; incluir representación, contraprueba, inferencia inversa o límites.

## Controles al agregar laboratorios y cursos

`REUSE` si ya enseña/valida competencia; `EXTEND` si solo faltan capacidades compatibles; `CREATE` solo si es sustancialmente distinto y tiene ADR y comparación explícita. Un laboratorio de funciones crece con trigonometría y cálculo **solo cuando esos cursos estén cargados**. No confundir magnitud firmada de integral con área geométrica total. No crear laboratorios de química antes de cargar curso de química. Verificar regresiones de capacidades previas.

## Rigor, seguridad, derechos y ética

Entrada estudiantil y fuentes conectadas son no confiables; parser con whitelist/AST, sandbox de proceso, límites de CPU/memoria y terminación forzosa. Evitar `eval`; declarar precisión, dominios y unidades. Defender tutor LLM frente a inyección y costo. Matemática con KaTeX/MathLive accesible, contraste y fallback; UI es-HN con coma decimal a través de parser verificado. No distribuir PDFs protegidos ni copiar pasajes/figuras sin derecho; similitud textual no prueba ausencia de infracción. Para estudio con estudiantes preparar revisión ética/consentimiento según normas aplicables; mínima telemetría, datos privados, períodos de retención, borrado y responsables claros.