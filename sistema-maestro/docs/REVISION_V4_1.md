# Cambios aprobados — Sistema Maestro v4.1

## Correcciones de cumplimiento
- El progreso y el dominio no son equivalentes. `MASTERED` deriva de evidencias verificadas, no de un string ni del reloj del dispositivo.
- La transferencia de la ruta utiliza un ítem distinto de los ítems reservados para examen; los oráculos y objetivos pueden compartirse.
- Los grants se conservan por unión monotónica; revisar idempotencia y referencias a evidencia; revisiones posteriores no retiran acceso.
- `NO_LAB` deja de ser un resultado de gate; `NOT_APPLICABLE` solo se permite con justificación técnica y contexto.
- Bootstrap de GitHub y Render ya realizado; `M0` sigue condicionado a `APROBAR_DISEÑO`. No crear un segundo repositorio.
- El orden de lectura y la autoridad normativa se centralizan en `CONSTITUCION.md`.
- El CI debe comprobar scripts, esquemas, rutas de continuidad y archivo de identidad; sus resultados no se confunden con revisión docente ni estudio empírico.
- `continuity.json` es un checkpoint, no evidencia en tiempo real. Los SHAs observados son snapshots; consultar la fuente correspondiente.

## Límite de la certificación
Los validadores actuales prueban estructura e invariantes de datos sintéticos. No implementan un motor científico, una base de datos de estudiantes ni una interfaz educativa funcional. El primer curso real sigue pendiente. Las pruebas locales, CI, Render y revisión académica deben reportarse por separado y asociarse al commit.
