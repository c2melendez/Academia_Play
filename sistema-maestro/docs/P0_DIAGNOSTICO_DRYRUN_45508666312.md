# P0 — Diagnóstico real de workflow_dispatch #45508666312 (2026-11-24)

## Evidencia de proveedor

- [GitHub Actions, corrida 45508666312](https://github.com/c2melendez/Academia_Play/actions/runs/45508666312), workflow `P0 - Authenticated reconciliation dry run`.
- Evento: `workflow_dispatch`; rama `main`; commit `150a48de8146bfc7bc59e48662c60b7880a1d6b5`.
- Resultado: `completed/failure`.
- Job `verify-reconciliation-dryrun`, ID `138850387895`.
- Pasos `Reject non-main dispatch` y `Verify provider credentials are configured`: `success`.
- Paso `Authenticated read-only reconciliation`: `failure`.
- Error exacto visible en el log: `ModuleNotFoundError: No module named 'jsonschema'`, al importar `validate_academia_play.py` desde el script de reconciliación.
- **No se realizaron verificaciones autenticadas de CI/Render desde el script**: el proceso terminó durante sus importaciones. No se produjo `DRY_RUN`, PR ni cambios sobre `main`.

## Causa y corrección

El workflow configuraba Python 3.12, pero omitía instalar las dependencias que el workflow de contratos sí instala. Se añadió antes de la ejecución autenticada:

```yaml
- name: Install validator dependencies
  run: python -m pip install -r sistema-maestro/requirements-dev.txt
```

La suite `test_reconciliation_dispatch.py` ahora exige que la instalación preceda a la ejecución del script. El flujo continúa exclusivamente manual, sin credenciales persistidas en checkout ni permiso de escritura.

## Próximo ensayo

Al integrarse este cambio por PR y confirmarse CI `success` más Render `live` para el mismo SHA de `main`, volver a iniciar el workflow manual con el **run ID del CI del nuevo HEAD**, no con `45457034682` del commit anterior. Registrar `DRY_RUN` solo cuando el propio workflow termine con éxito y el script publique ese resultado.

No se ha declarado E1 de reconciliación autenticada. La revisión humana independiente sigue siendo un control pendiente de P0.
