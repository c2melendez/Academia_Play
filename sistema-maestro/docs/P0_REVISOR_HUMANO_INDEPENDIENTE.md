# P0 — Habilitación verificable de revisión humana independiente

**Estado al 24-11-2026:** `BLOCKED_REVIEWER_CAPACITY`; no atribuir aprobación humana a un LLM ni al autor de sus propios cambios.

## Evidencia observada

- Ruleset [27979930](https://github.com/c2melendez/Academia_Play/rules/27979930) en `main`: `enforcement=active`, `contracts` obligatorio y PR obligatorio, `required_approving_review_count=0`, sin `require_code_owner_review` ni `dismiss_stale_reviews_on_push`; `bypass_actors=[]`.
- Consultas de revisiones del [PR #18](https://github.com/c2melendez/Academia_Play/pull/18) y [PR #19](https://github.com/c2melendez/Academia_Play/pull/19): arreglos vacíos `[]`.
- `c2melendez` tiene permiso `admin` en el repositorio; **esto no demuestra una segunda persona autorizada**, ni una aprobación independiente en un PR determinado.
- Con la conexión disponible no se obtuvo un listado verificable de todos los colaboradores; no afirmar que no existe ningún otro colaborador. Capacidad independiente: **NO_VERIFICADA**.

## Procedimiento administrativo, en orden (evitar bloqueo)

1. Elegir **una persona real distinta del autor** que pueda revisar cambios normativos, contratos, workflows y continuidad. Solicitar su aceptación de la función de revisión.
2. En [Settings → Collaborators](https://github.com/c2melendez/Academia_Play/settings/access) invitar su cuenta GitHub y confirmar aceptación, permisos efectivos y capacidad para revisar el repositorio. Usar mínimos privilegios compatibles; no otorgar administración sin necesidad.
3. Crear un PR de prueba sobre una rama aislada que modifique exclusivamente documentación de gobernanza y solicitarle su revisión. Registrar en la API de GitHub el usuario revisor, `state=APPROVED`, `commit_id` igual al HEAD exacto, y verificar que no sea autor ni cuenta automatizada. **No presentar una aprobación de un PR antiguo como autorización para uno nuevo.**
4. Preparar `.github/CODEOWNERS` asignando rutas normativas a una **cuenta real comprobada**; no usar nombres ficticios, del propio autor o de bots para simular independencia. Verificar que GitHub reconozca al code owner.
5. Solo después de verificar los puntos anteriores, editar el ruleset activo [27979930](https://github.com/c2melendez/Academia_Play/rules/27979930) manteniendo PR, `contracts`, squash y sin bypass: exigir **al menos 1 aprobación**, **Code Owners** y **Dismiss stale pull request approvals when new commits are pushed**. Guardar y consultar las reglas de la API; verificar que las opciones fueron aplicadas.
6. Ensayar que GitHub rechace realmente un PR con `contracts` exitoso pero sin aprobación independiente y permita integrar uno revisado correctamente. Cerrar sin fusionar el PR de prueba negativa; no habilitar autoaprobaciones.
7. Ejecutar el auditor de reglas `sistema-maestro/scripts/branch_protection_audit.py` **solo con identidades humanas verificadas**. Aun con reglas estáticas correctas, el PASS de un auditor no sustituye pruebas reales ni una revisión humana de cada PR normativo.

## Qué está autorizado hoy y qué queda bloqueado

La protección CI y la persistencia observada por conectores en el PR #19 cuentan con evidencia propia. La ejecución real de `submit_reconciliation_pr.py` sin `--dry-run` tampoco ha sido acreditada. **La aprobación humana independiente permanece BLOCKED**. No transformar retrospectivamente PR #18/#19 en revisados, ni marcar `G-ACADEMIC` o `APROBAR_DISEÑO` como aprobados: éstos requieren fuentes y proceso pedagógico independientes.

## Criterio de aceptación

**VERIFIED_REVIEWER_CAPACITY** requiere: otra persona con permiso aceptado; un PR real con aprobación vigente para SHA exacto y distinto autor; ruleset con 1+ aprobación y CODEOWNERS/stale dismissal activos; pruebas negativa y positiva de aplicación. Hasta entonces, mantener `BLOCKED_REVIEWER_CAPACITY`.
