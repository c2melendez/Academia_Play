# Academia Play — Sistema Maestro v4.1

**Fuente normativa vigente de Academia Play.** El repositorio GitHub `c2melendez/Academia_Play` y su rama predeterminada prevalecen sobre adjuntos de chats y archivos históricos.

## Lectura obligatoria para un agente

1. [CONSTITUCION.md](CONSTITUCION.md): orden canónico de lectura y principios.
2. [RUNBOOK.md](RUNBOOK.md): procedimientos de ejecución.
3. [GATES.md](GATES.md): catálogo de validación.
4. [schemas/](schemas/): contratos estructurales.
5. [PROMPT_MAESTRO.md](PROMPT_MAESTRO.md): activación del ejecutor.
6. [AGENTS.md](AGENTS.md): instrucciones de reanudación.
7. [../continuity.json](../continuity.json): estado observado (checkpoint).
8. [../infra/](../infra/): infraestructura y manifiesto activo.

## Estructura

- `schemas/`: JSON Schema Draft 2020-12 de manifiestos, progreso, gates, continuidad y eventos.
- `scripts/build_contracts.py`: genera los esquemas canónicos (verificar diferencias antes de publicar).
- `scripts/validate_academia_play.py`: validación estructural e integridad referencial.
- `tests/test_contracts.py`: pruebas positivas y negativas.
- `examples/`: datos sintéticos; NO representan sílabos reales de la UNAH.
- `docs/`: contexto y estrategia; `archive/` conserva solo antecedentes históricos.

## Pruebas

```sh
python -m pip install -r sistema-maestro/requirements-dev.txt
python -m unittest discover -s sistema-maestro/tests -v
python sistema-maestro/scripts/validate_academia_play.py sistema-maestro/examples/manifest.json
python sistema-maestro/scripts/validate_academia_play.py sistema-maestro/examples/progress.json --kind progress
python sistema-maestro/scripts/validate_academia_play.py sistema-maestro/examples/gate.json --kind gate
```

La aprobación estructural no demuestra exactitud de un motor científico, resultados de aprendizaje, validez académica ni despliegue.
