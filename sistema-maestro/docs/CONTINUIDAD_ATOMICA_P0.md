# P0 — Reconciliación persistente, concurrencia e idempotencia

## Contrato operacional

El comando `RECONCILIAR` conserva su definición normativa en el Runbook. La implementación optativa `scripts/persist_reconciliation.py` hace lo siguiente:

1. Recibe el **HEAD exacto previo** de `main` y el ID de una corrida GitHub Actions.
2. Comprueba si ya existe un evento determinista `RECONCILIAR-<sha>-<run_id>`. Si existe y coincide, devuelve `ALREADY_RECORDED` sin escribir ni atribuir vigencia al estado histórico.
3. Consulta el HEAD actual y rechaza discrepancias (`ConcurrentUpdate`).
4. Obtiene evidencia de GitHub CI y Render **directamente** mediante `provider_evidence.observe`, usando credenciales seguras. No acepta archivos JSON de agentes como origen de evidencia E1.
5. Construye tres archivos en una única operación Git: `continuity.json`, `sistema-maestro/execution-events/reconcile-<sha>-<run_id>.json` y `...observation.json`.
6. Recomprueba HEAD, crea un único árbol y commit con padre conocido, y actualiza `refs/heads/main` con `force=false`. Si otro agente avanzó la rama, rechaza la operación.
7. Preserva estados curriculares, aprobación, bloqueo y próxima acción: **no aprueba M0 ni cambia un gate a PASS**.

## Ejecución explícita

Requiere `GITHUB_TOKEN` con acceso de lectura de CI y escritura de contenidos de este repositorio, y `RENDER_API_KEY` de solo lectura, cargados por mecanismos seguros. No colocar tokens en código, argumentos ni archivos del repositorio.

```bash
python sistema-maestro/scripts/persist_reconciliation.py --expected-head <SHA_COMPLETO> --run-id <RUN_ID> --dry-run
python sistema-maestro/scripts/persist_reconciliation.py --expected-head <SHA_COMPLETO> --run-id <RUN_ID>
```

No ejecutar automáticamente en cada `push` ni crear un bucle de auto-commits. Las reglas de protección pueden exigir PR y rechazar la actualización directa: en ese caso **detenerse**, no forzar la rama ni desactivar protecciones. El comando `--dry-run` verifica los proveedores y prepara cambios sin escribir objetos Git.

## Semántica importante

El SHA registrado en `continuity.json` representa el commit **verificado antes de la escritura**. La operación de persistencia genera otro commit, que todavía no tiene CI o despliegue demostrados. El checkpoint es una observación histórica fechada, no una afirmación de que HEAD nuevo esté desplegado. La fecha `last_verified_deploy_at` se obtiene del `finishedAt` del proveedor Render; si no existe, queda `null`, nunca se inventa.

El evento y la observación se publican atómicamente con el checkpoint. Si la sesión se interrumpe antes de actualizar la ref de GitHub, ninguno de los tres archivos queda publicado; si termina después, una repetición detecta `ALREADY_RECORDED`. Los objetos Git inalcanzables creados antes de un conflicto no son historial publicado.

## Controles y límites

- Sin acceso autenticado o permisos para escribir: `BLOCKED`.
- Otro escritor adelantó HEAD: `ConcurrentUpdate`, detener y reconciliar desde cero.
- CI fallido, SHA desigual, despliegue no LIVE, repositorio o servicio distinto: sin persistencia.
- Un evento publicado identifica una observación histórica E1 de proveedores, **no la certificación de un módulo educativo**.
- `CODEOWNERS` requiere configuración independiente de protección de rama, aún no acreditada.
- En el flujo actual, CI prueba la lógica con mocks; **no se ha ejecutado automáticamente la escritura de producción**.
- El campo `repo_head_sha` en el checkpoint no debe tratarse como HEAD actual una vez que se crea un nuevo commit. Su nombre legado debe interpretarse como «HEAD observado al realizar el checkpoint».

La implementación no sustituye la futura validación de firmas humanas ni la certificación académica o empírica.
