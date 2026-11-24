# P0 — Protección normativa y aprobaciones verificables

## Distinción de autoridades

1. **Gobernanza GitHub:** un PR que afecta Constitución, Runbook, gates, validadores, CI, continuidad o infraestructura requiere revisión autorizada según la política de repositorio. `scripts/governance_review.py` comprueba por API de GitHub el PR, su HEAD exacto, la revisión `APPROVED`, la identidad autorizada y la independencia respecto al autor. Una revisión `DISMISSED`, `CHANGES_REQUESTED`, de otro commit o del propio autor se rechaza.
2. **Aprobación curricular:** `APROBAR_DISEÑO` permanece reservada a instrucción explícita del usuario por canal confiable para una revisión específica del diseño. **Un PR, review, issue, PDF, manifiesto JSON o comentario no crea esa autorización.** El verificador GitHub no puede sustituirla.
3. **Certificación académica:** la revisión docente necesita su propia evidencia e identidad. No se concede al ejecutar CI.

## Uso de consulta (sin escritura)

```bash
GITHUB_TOKEN=<token-gestionado-externamente> python sistema-maestro/scripts/governance_review.py --pr <NUMERO>
```

Usar tokens de solo lectura y un gestor seguro; no colocar tokens en línea de comandos en un entorno compartido. El resultado `VERIFIED_REVIEW` solo acredita una revisión de gobernanza que corresponde al HEAD del PR en el momento de consulta. Un commit posterior exige otra revisión. `NOT_APPLICABLE` significa que no hay archivos sensibles entre los archivos cambiados; no equivale a aprobación docente.

## Protección efectiva pendiente de configurar/verificar

La presencia de `.github/CODEOWNERS` no obliga por sí sola al propietario a revisar. Con cuenta que tenga permisos administrativos, configurar en GitHub **Settings → Rules → Rulesets** (o protección de rama equivalente) para `main`:

- Impedir el push directo y exigir PR antes de integrar, incluso para automatizaciones, salvo excepciones justificadas y auditables.
- Requerir el estado exitoso del workflow `Academia Play v4.1 — contract QA` y revisión de personas con permiso correspondiente.
- Exigir revisión de CODEOWNERS para archivos de gobernanza, impedir que los autores aprueben sus propios cambios, descartar aprobaciones cuando cambie el HEAD.
- Limitar excepciones, exigir conversaciones resueltas y preservar logs de auditoría.
- **No desactivar estas salvaguardas para conseguir CI verde.**

**Advertencia operativa:** el repositorio parece gestionado actualmente por un único propietario `@c2melendez`. Una regla de revisión independiente puede hacer imposible integrar cambios realizados por ese mismo propietario sin agregar un segundo revisor humano autorizado. Diseñar ese mecanismo antes de activar reglas obligatorias; jamás sustituirlo por una revisión ficticia.

## Situación observada

Al realizar esta revisión, el endpoint de reglas de repositorio devolvió lista vacía y la lectura de protección de rama fue previamente rechazada por falta de acceso administrativo. Por tanto **no se declara protección activada**. La conexión de GitHub disponible no permite escribir reglas de protección. Este bloqueo se considera de configuración externa, no un fallo de CI.

## Pruebas y aceptación

`test_governance_review.py` utiliza fixtures sintéticos y exige rechazar: ausencia de revisión, autor igual al revisor, SHA obsoleto, revisión desestimada, solicitud de cambios posterior, identidad no autorizada, PR en borrador y destino distinto de `main`. Las pruebas no equivalen a activar la protección efectiva en la interfaz de GitHub.

Antes de cerrar P0: (a) verificar reglas activas por una cuenta administradora, (b) probar que un PR sensible no puede fusionarse sin revisión válida, (c) observar que CI requerido pasa, (d) demostrar que la aprobación curricular sigue dependiendo de `APROBAR_DISEÑO` explícito y no puede ser atribuida al ejecutor.
