# P0 — Verificación externa de CI y despliegue

## Alcance

`scripts/provider_evidence.py` consulta **en modo solo lectura** GitHub y Render para comparar:

- Identidad del repositorio `c2melendez/Academia_Play` y rama `main`.
- GitHub Actions `status=completed`, `conclusion=success`, `head_sha` exacto y repositorio de la corrida.
- Servicio Render `srv-dc06lp67bikc739hlghg`, repositorio y rama enlazados.
- **Último** despliegue Render con estado `live`, ID y SHA exacto del objetivo.

Este chequeo prueba solamente la correspondencia de las observaciones de proveedor con el SHA solicitado. **No prueba** que el contenido curricular, oráculos, seguridad, accesibilidad o aprendizaje estén certificados. Nunca sustituir por un `G-DEPLOY=PASS` automático.

## Ejecución autenticada

En un entorno autorizado, configurar `GITHUB_TOKEN` de solo lectura y `RENDER_API_KEY` en el gestor seguro de secretos (nunca en argumentos ni repositorio). Ejecutar:

```bash
python sistema-maestro/scripts/provider_evidence.py --sha <COMMIT_SHA_DE_40_CARACTERES> --run-id <ID_CORRIDA>
```

El proceso devuelve `VERIFIED_OBSERVATION`, `REJECTED_OBSERVATION` o `BLOCKED`; cualquier error debe dejar el gate sin aprobar. No copiar ni versionar secretos.

Para comparar una observación autenticada almacenada temporalmente fuera del repositorio:

```bash
python sistema-maestro/scripts/reconcile_observation.py --continuity continuity.json --observation <ARCHIVO_JSON_TEMPORAL>
```

La comparación es **solo lectura**: produce un listado de diferencias, sin editar `continuity.json` ni declarar aprobación de diseño. El resultado JSON obtenido de fuentes externas no es automáticamente confiable: debe preservarse su procedencia, ejecutarse el verificador autenticado y vincular el registro a la corrida correspondiente.

## CI y limitaciones

GitHub Actions ejecuta las pruebas con fixtures sintéticos **sin usar tokens externos ni consultar Render**. Un CI verde certifica las comprobaciones estructurales y los escenarios simulados, no la disponibilidad o corrección de la infraestructura externa. La verificación autenticada se ejecuta al reconciliar o publicar, respetando los permisos del entorno.

Una diferencia entre observación actual y snapshot histórico es `STALE`, nunca evidencia de dos despliegues simultáneos. La actualización persistente, las aprobaciones humanas y el control de concurrencia requieren el siguiente tramo P0; este lote no les atribuye implementación.
