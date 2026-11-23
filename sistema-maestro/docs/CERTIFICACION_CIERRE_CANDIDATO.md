# Comprobación estructural del cierre técnico (P0)

`scripts/gate_coverage.py` evalúa cobertura de gates y compatibilidad de SHA para un candidato `DONE_TECHNICAL`. No consulta APIs, no comprueba autenticidad de los logs y **no certifica** por sí mismo evidencia E1.

El cierre real también exige observar GitHub Actions, Render y las revisiones humanas aplicables, de acuerdo con `GATES.md`. En ausencia de esa comprobación externa se mantiene el estado de evidencia no verificada y no se anuncia módulo técnico aprobado.

Las excepciones `G-LAB` y `G-A11Y-MANUAL` exigen registros `NOT_APPLICABLE` justificados cuando el catálogo los permite. La aplicabilidad de otras gates y las reglas de aprobación continúan siendo responsabilidad normativa de `GATES.md` y `CONSTITUCION.md`.

No sustituir este análisis estructural por una declaración `PASS` del agente.
