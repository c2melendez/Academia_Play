# P0 — Identidad del workflow de CI y evidencia de reconciliación

## Comprobación realizada el 24 de noviembre de 2026

La API GitHub observó:

- Repositorio: `c2melendez/Academia_Play`
- `main`: `1e139efcf423c1623676b2681a4e4ead698976b4`
- Corrida `45455607193`: `completed/success`, evento `push`, rama `main`, SHA coincidente.
- Identidad de workflow: `425123083`, archivo `.github/workflows/academia-play-contracts.yml`.
- Ruleset `27979930`: `active`, PR y `contracts` obligatorios, cero bypass.
- No se encontró prueba de ejecución manual autenticada de `p0-reconciliation-dryrun.yml` en los runs recientes examinados. La falta de una corrida observada **no demuestra que nunca haya existido**; no declarar E1 hasta obtener su ID y revisar el resultado.

## Riesgo resuelto en verificador

Una corrida **exitosa de otro workflow** sobre el mismo SHA no demuestra que el contrato `contracts` pasó. Se ha fortalecido `provider_evidence.verify_observations` para exigir `workflow_id=425123083`, `path=.github/workflows/academia-play-contracts.yml`, evento `push` y rama `main`, además de las condiciones previas de identidad, SHA y despliegue Render LIVE.

Las pruebas negativas rechazan otro ID, otra ruta, evento PR, otra rama y campos ausentes. Si se reemplaza el workflow y GitHub le asigna otro ID, se deberá actualizar esta identidad con evidencia verificada: **un cambio de ID nunca se acepta automáticamente**.

## Próximo paso operativo sin revelar secretos

El workflow manual `.github/workflows/p0-reconciliation-dryrun.yml` se puede iniciar desde la pestaña Actions, seleccionando `main`, luego `P0 - Authenticated reconciliation dry run`, e ingresando el ID de una corrida `contracts` exitoso para el mismo HEAD. Requiere que un administrador configure previamente el secret `RENDER_API_KEY` en Actions.

El script ejecuta `--dry-run`, lee los proveedores y prepara la propuesta, **sin escribir** ramas, commits, PR ni checkpoints. Para acreditar E1 de esta prueba debe observarse su salida `DRY_RUN` en la corrida real. Sin secreto o sin ejecución, el estado sigue `NOT_RUN/BLOCKED`; no utilizar fixtures de CI como sustituto.

La conexión GitHub disponible en esta intervención no expone una acción para iniciar un `workflow_dispatch` ni para administrar el secreto, por lo que no se ha generado o simulado esa ejecución.

La revisión humana independiente para cambios normativos continúa pendiente; ninguna aprobación curricular `APROBAR_DISEÑO` está implícita.
