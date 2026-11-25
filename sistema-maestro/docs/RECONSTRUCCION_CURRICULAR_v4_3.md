# Academia Play v4.3 — investigación y reconstrucción curricular autónoma

## Propósito
Eliminar el bloqueo de exigir un sílabo oficial único aportado por el usuario. Basta institución y asignatura para **iniciar investigación**; el usuario proporcionará libros y ediciones disponibles para contrastar y construir materiales. No presumir que el curso reconstruido es oficial.

## Tres rutas de fuente
- **OFFICIAL_VERIFIED:** sílabo/programa emitido por una dependencia institucional, edición, fecha y alcance corroborados. Un programa antiguo puede ser auténtico sin ser vigente; declarar esa limitación.
- **RECONSTRUCTED_PROPOSED:** programa inferido y triangulado, procedencia y divergencias explícitas, pendiente de aprobación humana para uso en Academia Play.
- **RESEARCH_INSUFFICIENT:** fuentes inaccesibles, contradictorias o demasiado limitadas; solo investigación y prototipo sintético, sin certificar cobertura.

## Búsqueda disciplinada
1. Identificar nombre/código, institución, carrera, campus y período cuando existan; no confundir asignaturas homónimas.
2. Priorizar webs institucionales, programas de facultad, catálogos, bibliotecas y archivos académicos; contrastar versiones históricas.
3. Complementar con repositorios y sitios comunitarios (Studocu, Scribd, Course Hero, College Sidekick, Docsity y otros); registrar barreras de acceso, legitimidad y calidad. Evitar eludir accesos, copiar material protegido o afirmar lectura no realizada.
4. Buscar equivalentes interuniversitarios por **objetivos, horas, prerrequisitos, nivel y profundidad**, nunca solo por nombre.
5. Desduplicar documentos de origen común y fijar fecha de observación, URL y evidencia legible, página/sección cuando exista. Una lista de diez copias no equivale a diez fuentes independientes.
6. Triangular cada unidad/competencia, distinguir núcleo estable, variaciones docentes, bibliografía alternativa e inferencias académicas.
7. Contrastar con libros aportados: autor/edición/capítulo/sección/páginas y nivel; un texto no es un sílabo. Las referencias de varias ediciones son sustituibles solo después de inspección.
8. Entregar propuesta ordenada, contradicciones, incertidumbres y mapa FUNDAMENTO → PUENTE → COMPETENCIA → TRANSFERENCIA, junto a evidencia pedagógica específica. Presentar tres diseños didácticos por familia, uno sin simulación.
9. Solicitar APROBAR_DISEÑO exacto del usuario; esa aprobación adoptará el programa **para la plataforma**, no otorgará autenticidad institucional ni firma docente.
10. Implementar primera experiencia después de la aprobación y la migración contractual del manifiesto, verificando funcionalidad y transferencia antes de ampliar gobernanza.

## Matriz de trazabilidad obligatoria
Cada afirmación curricular: identificador, texto y alcance, clase de evidencia (INSTITUTIONALLY_CONFIRMED, DOCUMENT_CORROBORATED, ACADEMICALLY_INFERRED, UNRESOLVED), fuentes independientes inspeccionadas, variantes/contradicciones, nivel de confianza justificado, impacto en fundamentos y decisión de incluir/excluir. La clasificación se refiere a **esa afirmación**, no al programa completo. No convertir ausencia de disputa en confirmación institucional.

En `schemas/reconstructed_curriculum.schema.json` se define el expediente de investigación **separado** de `manifest.schema.json` v4.1 para mantener retrocompatibilidad. Ninguna validación estructural autentica fuentes: sus identificadores y citas deben confrontarse con documentos realmente consultados. `RECONSTRUCTED_PROPOSED` no habilita implementación M0 por sí solo.

## Compatibilidad y migración controlada
- Mantener `continuity.json` y sus estados existentes hasta que haya un expediente curricular real autorizado y una ruta de migración probada.
- `COURSE_PENDING` / `SOURCE_MISSING` siguen indicando ausencia de evidencia curricular/aprobación suficientes; **no detienen la investigación**.
- Antes de crear manifiesto de curso reconstruido, adaptar `course.syllabus_source_id` y el validador para referir un expediente `RECONSTRUCTED` real sin forzar el tipo `SYLLABUS`, con fixtures negativos. Esta actualización se hará con primer curso aprobado, no fabricando un registro oficial.
- No cambiar protección de ramas, proveedores, secretos ni certificaciones para acelerar investigación pedagógica.

## Entrega inicial MM-110 (próxima acción real)
Entrada conocida: UNAH, MM-110 Matemática I. Investigar programa y versiones con comparación documental; solicitar libros/ediciones para análisis de capítulos y páginas. Resultado: expediente reconstruido **solo con fuentes realmente abiertas**, mapa fundacional y propuesta humana. No afirmar hoy que MM-110 dispone de sílabo oficial único, ni que una bibliografía es obligatoria para todos los docentes.

## Prueba de aceptación
Una búsqueda de fuentes inaccesibles no produce citas inventadas; una unidad basada únicamente en otro centro universitario conserva ACADEMICALLY_INFERRED; dos copias del mismo documento no son corroboración independiente; una contradicción relevante no se resuelve por mayoría artificial; una aprobación de usuario no modifica institucionalidad; un nuevo libro no reescribe automáticamente competencias. La primera experiencia interactiva depende de aprobación curricular exacta y validación científica de su contenido.
