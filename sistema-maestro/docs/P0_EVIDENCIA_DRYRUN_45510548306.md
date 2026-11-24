# P0 — Evidencia E1: reconciliación autenticada en modo DRY_RUN

**Fecha:** 2026-11-24. **Resultado:** `E1_DRY_RUN_VERIFIED` (alcance limitado a preparación autenticada de la propuesta, sin escrituras).

## Fuentes observadas directamente en proveedores

- [GitHub Actions: workflow_dispatch 45510548306](https://github.com/c2melendez/Academia_Play/actions/runs/45510548306), workflow `P0 - Authenticated reconciliation dry run`; `completed/success`; HEAD `3718d6d99a9a03fc5e00b1b0d773e00d2ab651a1`, rama `main`.
- Job `verify-reconciliation-dryrun` (ID `138856862375`): `completed/success`. Los pasos `Install validator dependencies`, `Verify provider credentials are configured`, `Authenticated read-only reconciliation` y `Preserve no-write scope` terminaron todos con `success`.
- La salida **real del script** `submit_reconciliation_pr.py --dry-run` contiene `"result": "DRY_RUN"`, `"observed_sha": "3718d6d99a9a03fc5e00b1b0d773e00d2ab651a1"` y `"note": "Authenticated provider observations; no commits/branches/PRs created"`.
- El run ID del workflow canónico `contracts` suministrado fue `45509378958`, perteneciente al commit observado; el verificador validó GitHub y Render con sus credenciales.
- En la observación adicional se confirmó `main.protected=true` y `ruleset 27979930` activo con `contracts` obligatorio, sin bypass. El despliegue Render del SHA observado era `live` (`dep-dc31o8o473hc73bkcgmg`).

## Archivos preparados, no publicados

`DRY_RUN` enumeró exactamente:

1. `continuity.json`
2. `sistema-maestro/execution-events/reconcile-3718d6d99a9a03fc5e00b1b0d773e00d2ab651a1-45509378958.json`
3. `sistema-maestro/execution-events/reconcile-3718d6d99a9a03fc5e00b1b0d773e00d2ab651a1-45509378958.observation.json`

El script **no creó** rama, commit ni pull request, ni escribió en `main`. El evento y snapshot se prepararon en memoria; la publicación persistente sigue pendiente. Los resultados solo certifican el SHA observado **antes** de una eventual escritura.

## Criterio de cierre e incertidumbre residual

**APROBADO:** ensayo operativo autenticado de solo lectura para GitHub/Render y generación validada de propuesta en modo DRY_RUN (evidencia E1 respaldada por corrida real y logs). Esto supera el fallo previo de importación `jsonschema` observado en [45508666312](https://github.com/c2melendez/Academia_Play/actions/runs/45508666312).

**PENDIENTES, NO APROBADOS POR ESTA PRUEBA:**

- Ejecutar una propuesta **con escritura** mediante `submit_reconciliation_pr.py` con credenciales autorizadas, PR normal y verificaciones de protección; comprobar la publicación y conciliación final del nuevo SHA. No usar `GITHUB_TOKEN` de solo lectura del workflow DRY_RUN para ello.
- Acreditar la existencia de **revisor humano independiente** y activar la exigencia de aprobación/Code Owners/stale review cuando la capacidad esté realmente habilitada.
- Aprobar diseño/currículo M0 solo con fuentes académicas reales; no confundir evidencia de proveedores con autorización educativa.

Al integrar este expediente se creará otro commit; **el SHA anterior del DRY_RUN es evidencia histórica y no prueba que el nuevo HEAD esté desplegado**. Verificar GitHub Actions y Render de ese nuevo SHA por separado.
