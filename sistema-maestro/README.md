# Academia Play — Sistema Maestro v4.0

**Fuente normativa vigente de Academia Play.** El repositorio GitHub `c2melendez/Academia_Play` y su rama predeterminada prevalecen sobre adjuntos de chats y archivos históricos.

## Lectura obligatoria para un agente

1. [CONSTITUCION.md](CONSTITUCION.md): reglas no negociables y prioridad.
2. [PROMPT_MAESTRO.md](PROMPT_MAESTRO.md): misión y arranque.
3. [RUNBOOK.md](RUNBOOK.md): comandos, autonomía y persistencia.
4. [GATES.md](GATES.md): validación técnica, académica y empírica.
5. [AGENTS.md](AGENTS.md): continuidad.

## Estructura

- `schemas/`: JSON Schema Draft 2020-12 de manifiestos, progreso y gates.
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
