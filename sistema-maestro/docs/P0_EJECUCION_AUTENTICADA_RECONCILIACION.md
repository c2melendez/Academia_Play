# P0 — Ejecución autenticada de reconciliación sin escritura

## Propósito

Permitir ejecutar **el código real** `submit_reconciliation_pr.py` desde GitHub Actions, con datos consultados directamente a GitHub y Render, manteniendo el modo `--dry-run` para no eludir el ruleset de `main`.

Workflow: `.github/workflows/p0-reconciliation-dryrun.yml`. Se inicia **manualmente**, nunca con push, cron ni desde el workflow de contratos. El workflow requiere permisos GitHub `contents: read` y `actions: read`; no dispone de permisos de escritura de PR.

## Preparación administrativa

1. En **Settings → Secrets and variables → Actions**, configurar `RENDER_API_KEY` como secreto del repositorio para una credencial Render con mínimo privilegio permitido por el proveedor. Nunca incluirla en comandos, PR, archivos del repositorio o capturas.
2. Confirmar que GitHub Actions tenga acceso de lectura a información de CI mediante `GITHUB_TOKEN` de la propia corrida.
3. Esperar hasta que el último commit de `main` tenga **CI completed/success** y despliegue Render `live` con SHA idéntico.
4. En **Actions → P0 - Authenticated reconciliation dry run → Run workflow**, seleccionar la rama `main` e introducir el **ID de la corrida CI del último SHA**, no el de un commit antiguo.
5. Inspeccionar las salidas de la corrida: `DRY_RUN` certifica que la consulta autenticada y la preparación de cambios funcionaron **sin escrituras**. Cualquier error es `BLOCKED`; no inventar cumplimiento.

## Limitaciones y seguimiento

- La existencia de este workflow y su CI sintético exitoso **no demuestra** que se haya ejecutado un dry-run autenticado.
- El secreto `RENDER_API_KEY` no puede leerse desde este asistente y **no se presupone existente**. Si falta, el job falla expresamente sin hacer cambios.
- La comprobación de la ejecución de GitHub/Render para un SHA no constituye aprobación académica, técnica de módulo ni autorización curricular.
- El workflow no genera un PR; publicar requiere ejecutar el comando `submit_reconciliation_pr.py` en un entorno con credenciales de escritura compatibles, o un conector confiable que conserve revisión y checks obligatorios.
- El token predeterminado `GITHUB_TOKEN` no debe utilizarse para crear PR esperando que esos eventos disparen nuevos workflows: si se usa automatización de propuesta, requiere un mecanismo seguro de emisión y comprobación de CI independiente.
- Registrar el run real y el SHA en el acta P0 **únicamente después de observarla**. No copiar secretos ni afirmar que el checkpoint histórico es el HEAD actual.

## Avances validados al incorporar este flujo

- Ruleset `27979930` activo, exige PR y check `contracts`, sin bypass.
- PR negativo #13: check `contracts` fallido, GitHub rechazó merge por HTTP 405; cerrado sin integrar.
- PR positivo #14: `contracts` exitoso e integrado.
- El primer ensayo autenticado de la nueva acción queda pendiente hasta su ejecución real.
