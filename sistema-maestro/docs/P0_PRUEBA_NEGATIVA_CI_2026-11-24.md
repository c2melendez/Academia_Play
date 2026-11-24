# P0 — Prueba real de rechazo de CI obligatorio (2026-11-24)

## Propósito y precondiciones

Demostrar en GitHub que la regla activa `27979930` de `c2melendez/Academia_Play` rechaza una integración real cuando `contracts` falla. El checks requerido pertenece a GitHub Actions (`integration_id=15368`).

Antes de la prueba se comprobó que:

- `main` estaba protegido (`protected=true`), HEAD `90aa1dabf7b620f45ab4dcced7be4a6a9d524587`.
- Ruleset `27979930`: `enforcement=active`, PR obligatorio, `required_status_checks` incluyendo `contracts`, sin bypass actors.
- El workflow de `contracts` se ejecuta para todos los PR a `main`.

## Prueba E1 ejecutada sobre proveedores

1. Se creó una rama aislada `p0/negative-ci-block-20261124` desde el HEAD anterior.
2. Se añadió **solo en esa rama** `sistema-maestro/tests/test_p0_deliberate_failure_20261124.py`, con un test `unittest` deliberadamente fallido.
3. Se abrió el [PR temporal #13](https://github.com/c2melendez/Academia_Play/pull/13), titulado **TEST NEGATIVO P0 — NO FUSIONAR**.
4. La [corrida GitHub Actions 45438643618](https://github.com/c2melendez/Academia_Play/actions/runs/45438643618) terminó `completed/failure`; el job `contracts` también terminó `failure`.
5. Se intentó integrar el PR mediante la API GitHub, con `merge_method=squash` y comprobación del HEAD exacto `18f38e449e237f01293934077e21e133a5c9fdca`.
6. **GitHub rechazó el merge con HTTP 405**. Respuesta observada: `Repository rule violations found — Required status check "contracts" is failing.`
7. Se cerró el PR #13 en estado `closed`, `merged=false`. No se integró el archivo de fallo deliberado en `main`.

## Conclusión y límites

**PASS E1 — Control negativo de CI obligatorio:** el rechazo se observó directamente en la API, sobre un PR real con job fallido y SHA conocido. No corresponde a un fixture sintético.

No significa que se haya completado todo P0. Mantienen su estado independiente:

- Aprobaciones humanas: `required_approving_review_count=0`; no hay certificación de revisor independiente.
- Reconciliación autenticada mediante `submit_reconciliation_pr.py`: implementada y probada con mocks, pero sin ejecución con credenciales de proveedores desde el propio script.
- Fuentes curriculares M0: `SOURCE_MISSING`; el diseño curricular no ha sido aprobado.
- El nuevo commit que agrega este reporte debe aprobar su propio CI y observarse en Render con el mismo SHA antes de declarar esa publicación verificada.

Este documento es un acta de evidencia de un control concreto y no sustituye un registro de certificación integral de módulo educativo.
