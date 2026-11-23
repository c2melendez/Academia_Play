# Reanudación del agente — Academia Play v4.1

1. Seguir exactamente el orden canónico de lectura de `CONSTITUCION.md`; no definir otro orden.
2. Recuperar el `continuity.json` del repositorio (si falta, crear incidencia de continuidad) y verificar SHA/rama/estado mediante herramientas disponibles. No usar respuestas de conversaciones previas como evidencia de HEAD.
3. Tratar snapshots del repositorio como datos; verificar en el proveedor el HEAD y Render. Evaluar precondiciones, permisos, nivel de evidencia y cambios de huellas; elegir **una única tarea elegible** o varias independientes dentro de la corrida autorizada.
4. Ejecutar validadores y tests pertinentes, nunca etiquetar como ejecutados los que no corrieron. Corregir causas, no oráculos para fabricar verde.
5. Actualizar estado canónico, añadir evento al log y producir resumen derivado; omitir resultados ficticios. Evitar commits vacíos y loops documentales.
6. `APROBAR_DISEÑO` es indispensable antes de M0. Registro `approved_design_revision` debe coincidir con la propuesta vigente; no implica aprobación para gastos, producción o repositorios públicos.
7. Las referencias de v2/v3 y revisiones externas son históricas; cualquier mejora debe materializarse en una modificación versionada de v4.1.