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

## Estado comprobado del ruleset

Al momento de esta entrega:

- `main.protected=true`; ruleset `27979930` activo y aplicable a la rama predeterminada.
- PR obligatorio, impedir eliminación y force push, conversaciones resueltas y squash.
- `required_approving_review_count=0`: no hay aprobación humana obligatoria todavía.
- Todavía **no existe** una regla `required_status_checks` para `contracts`, aunque el workflow se ejecuta en todos los PR.
- Sigue pendiente una segunda cuenta humana autorizada para revisiones normativas independientes. No se puede simular su autorización.

Configurar el status check `contracts` en [Ruleset 27979930](https://github.com/c2melendez/Academia_Play/rules/27979930) y comprobar por API que quedó obligatorio. No aumentar todavía aprobaciones sin habilitar segundo revisor.

## Aceptación y límites

La suite `test_submit_reconciliation_pr.py` usa mocks para garantizar: rechazo de evidencia inválida, bloqueo de SHA obsoleto, rama determinista, idempotencia ante evento/rama existentes, ausencia de escritura directa de `main` y PR sin auto-merge.

**Estas pruebas son E1 de ejecución de tests en CI**, no constituyen ejecución autenticada del comando contra proveedores. Esa corrida sigue pendiente y debe registrarse por separado.

P0 permanece abierto hasta exigir CI en GitHub, verificar la capacidad de revisión humana y observar una ejecución real de la reconciliación protegida.
