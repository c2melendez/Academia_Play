# P0 — Reconciliación por PR sobre main protegido

## Motivo

El 24 de noviembre de 2026 GitHub confirmó `main.protected=true` y la existencia del ruleset activo `27979930`. El mecanismo histórico `persist_reconciliation.py` intenta crear un commit directamente sobre `main`, por lo que **no es el camino operativo recomendado**. Nunca omitir la protección ni usar `force` para publicar continuidad.

## Flujo corregido

El nuevo comando `scripts/submit_reconciliation_pr.py`:

1. Requiere SHA exacto de `main`, run ID de GitHub Actions y credenciales externas `GITHUB_TOKEN` / `RENDER_API_KEY`.
2. Valida HEAD e impide un segundo registro del mismo evento.
3. Obtiene una observación autenticada de GitHub/Render en el mismo proceso; no acepta JSON autodeclarados.
4. Conserva estados curriculares y produce `continuity.json`, evento append-only y snapshot para el SHA **anterior**.
5. Comprueba nuevamente HEAD, crea un commit y una nueva rama `p0/reconcile-<SHA>-<RUN>` sin sobrescribir ramas existentes.
6. Abre un PR dirigido a `main`, que deberá superar los checks y requisitos de revisión exigidos por GitHub. **No fusiona automáticamente** ni atribuye al commit futuro un despliegue todavía no observado.

El flujo termina en `PROPOSED_NOT_MERGED`; se requiere PR normal. Una interrupción luego de crear la rama, pero antes de abrir el PR, deja la rama para inspección manual: reintentar no la sobrescribe.

## Uso

Cargar credenciales mediante un gestor seguro de secretos (nunca guardarlas en el repositorio).

```bash
python sistema-maestro/scripts/submit_reconciliation_pr.py --expected-head <SHA_40> --run-id <ID> --dry-run
python sistema-maestro/scripts/submit_reconciliation_pr.py --expected-head <SHA_40> --run-id <ID>
```

El modo `--dry-run` sí realiza consultas autenticadas, pero no escribe Git. En caso de `ConcurrentUpdate`, `BLOCKED` o error del proveedor, **reconsultar HEAD y CI/Render**, sin forzar un merge ni fabricar evidencia.

## Estado comprobado del ruleset — actualizado el 24 de noviembre de 2026

- `main.protected=true`; ruleset `27979930` activo, aplicable a `~DEFAULT_BRANCH`, sin actores de bypass.
- PR obligatorio, sin force push ni eliminación, conversaciones resueltas y merge por squash.
- **`contracts` sí es obligatorio** mediante `required_status_checks` con GitHub Actions; PR negativo #13 fue rechazado HTTP 405 y PR positivo #14 superó el control.
- `required_approving_review_count=0`, `require_code_owner_review=false` y `dismiss_stale_reviews_on_push=false`. No hay revisión humana obligatoria.
- Los PR #18 y #19 no muestran revisiones humanas; `c2melendez` es administrador pero no cuenta como segundo revisor independiente en los PR que el propio titular origina.
- Reconciliación autenticada `DRY_RUN` demostrada en Actions #45510548306; persistencia real por conectores GitHub/Render a través del PR #19. **La publicación por el CLI de escritura `submit_reconciliation_pr.py` sigue sin validarse con credenciales reales.**

**No activar una aprobación obligatoria sin comprobar previamente que existe al menos otra cuenta humana con permisos de revisión, acceso vigente y voluntad de revisar.** Siguiente procedimiento: [P0 — habilitación de revisor independiente](P0_REVISOR_HUMANO_INDEPENDIENTE.md).

## Aceptación y límites

La suite `test_submit_reconciliation_pr.py` usa mocks para garantizar: rechazo de evidencia inválida, bloqueo de SHA obsoleto, rama determinista, idempotencia ante evento/rama existentes, ausencia de escritura directa de `main` y PR sin auto-merge.

**Estas pruebas son E1 de ejecución de tests en CI**, no constituyen ejecución autenticada del comando contra proveedores. Esa corrida sigue pendiente y debe registrarse por separado.

Los controles de CI y la persistencia mediante PR protegido ya están verificados. P0 permanece abierto por la revisión humana independiente; el flujo CLI de escritura es una prueba adicional no realizada y no debe atribuirse a la ejecución basada en conectores.
