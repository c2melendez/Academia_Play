# Registro de verificación

El paquete v4.0 original aportó 25 pruebas positivas y negativas ejecutadas localmente. El estado actual de este repositorio debe verificarse mediante las corridas reales de GitHub Actions y los archivos publicados.

No usar este documento como prueba de CI o despliegue. Solo registrar PASS cuando el comando, su log, la revisión de aceptación y el commit SHA son comprobables. En ausencia de evidencia usar NOT_RUN, BLOCKED o PENDING_REVIEW según corresponda.

Para ejecutar manualmente:
```sh
python -m pip install -r sistema-maestro/requirements-dev.txt
python -m unittest discover -s sistema-maestro/tests -v
```
