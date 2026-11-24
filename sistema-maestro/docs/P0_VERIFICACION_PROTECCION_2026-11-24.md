# P0 — Auditoría de protección de `main` (2026-11-24)

## Resultado actual comprobado

- Repositorio: `c2melendez/Academia_Play`.
- `main`, HEAD observado antes de este cambio: `20791b84744bcd16f9bd7f7c3523a385f0c20a29`.
- La API de GitHub `GET /branches/main` devolvió **`protected: false`**.
- La API de GitHub `GET /rulesets` devolvió `[]`.
- El último CI observado del mismo HEAD fue **success**, pero eso no implica que sea obligatorio para fusionar.
- La conexión GitHub disponible **no expone acciones para configurar rulesets ni protección de rama**. No se ha activado protección.

**Resultado de aceptación AT-16:** `BLOCKED`. La afirmación «main está protegido» es falsa con esta evidencia.

## Auditor añadido

`scripts/branch_protection_audit.py` verifica reglas activas que afecten la rama predeterminada, PR obligatorio, aprobación humana, revisión de CODEOWNERS, descarte de revisiones obsoletas, CI `contracts` requerido y ausencia de excepciones de bypass conocidas. También requiere que se hayan verificado al menos dos cuentas humanas distintas. Si cualquier propiedad falta o la API devuelve error, emite `BLOCKED`.

```bash
python sistema-maestro/scripts/branch_protection_audit.py
```

Para observaciones autenticadas se necesita `GITHUB_TOKEN` de lectura con acceso a las reglas. Los valores suministrados como `--reviewer` deben haber sido corroborados por el administrador; **la presencia de cadenas en argumentos no constituye prueba de identidad o autorización**. Por eso un resultado local favorable tampoco sustituye una prueba remota de que GitHub rechaza realmente un PR sin revisión.

## Procedimiento administrativo pendiente

1. Designar un **segundo revisor humano autorizado** diferente del autor. No crear identidades de prueba ni atribuir aprobaciones inexistentes.
2. Configurar un ruleset de `main` con PR obligatorio, al menos una revisión, CODEOWNERS, descarte de aprobaciones obsoletas y estado requerido `contracts`, sin bypass que permita omitir la revisión.
3. Verificar en GitHub que el ruleset esté **active**, que efectivamente cubra `refs/heads/main` y que `main.protected` sea `true`.
4. Ensayar sobre un PR de prueba sin autorización la imposibilidad de fusionarlo, y demostrar que una aprobación válida de un revisor distinto habilita la fusión una vez aprobado CI.
5. Volver a ejecutar el auditor autenticado y archivar la prueba en un registro de evidencia de proveedor. Solo entonces podrá aprobarse AT-16.

**Advertencia:** en un repositorio con un único propietario, exigir revisión independiente puede detener todas las fusiones si se activa antes de habilitar al segundo revisor. La solución es asegurar ese permiso primero, no desactivar la norma ni usar una autorevisión.

## Alcance de esta entrega

El auditor y sus pruebas negativas son implementaciones técnicas, **no la activación de GitHub Rulesets**. El estado general de P0 permanece abierto mientras AT-16 y la ejecución real del script de persistencia no estén verificados. M0 curricular permanece sin aprobación y con fuentes pendientes.
