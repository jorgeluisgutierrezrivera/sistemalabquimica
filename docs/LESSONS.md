# Bitácora de Lecciones Aprendidas

> Registro de errores, sorpresas y decisiones no obvias surgidas durante el
> desarrollo. Cada entrada: **síntoma → causa → solución → cómo evitarlo**.
> Se añade una entrada cada vez que algo falla o se aprende algo reutilizable.

_Última actualización: 2026-06-25_

---

## L-001 · El launcher `py` está roto en esta máquina
- **Síntoma:** `py --version` → "El sistema no puede encontrar el archivo especificado".
- **Causa:** el launcher apunta a una ruta de Python inexistente.
- **Solución:** usar `python` (Python 3.13.14) o, dentro del proyecto, el
  intérprete del venv: `.\.venv\Scripts\python.exe`.
- **Evitar:** no invocar `py` en scripts ni comandos del proyecto.

## L-002 · `python -c "..."` multilínea falla en PowerShell
- **Síntoma:** `SyntaxError: '(' was never closed` al pasar código con comillas
  y `\` de continuación dentro de `python -c "..."`.
- **Causa:** PowerShell y el parser de Python pelean por el escape de comillas.
- **Solución:** usar un here-string canalizado —
  `@'`…código…`'@ | .\.venv\Scripts\python.exe -` — o un archivo `.py` temporal.
- **Evitar:** para cualquier script Python de más de una línea, archivo o here-string.

## L-003 · `CREATE TABLE IF NOT EXISTS` no aplica cambios de columnas
- **Síntoma:** tras editar una tabla en `schema.sql` y re-ejecutar `init_db`,
  la tabla seguía con la estructura vieja.
- **Causa:** `IF NOT EXISTS` omite la tabla si ya existe; no la altera.
- **Solución:** con la BD aún vacía, borrar `data/laboratorio.db` y regenerar.
  Cuando ya haya datos reales, se necesitará una **migración** explícita.
- **Evitar:** ante cambios de esquema, decidir entre "borrar+regenerar" (sin
  datos) o "migración" (con datos) — nunca asumir que `init_db` migra.

## L-004 · `LIKE COLLATE NOCASE` en SQLite no ignora acentos
- **Síntoma:** buscar `organica` no encontraba la materia "Química Orgánica I"
  (una prueba del M3 falló).
- **Causa:** el `NOCASE` de SQLite solo pliega mayúsculas/minúsculas ASCII; las
  vocales con tilde (á, é, í…) se tratan como caracteres distintos.
- **Solución (por ahora):** la búsqueda funciona case-insensitive pero es
  sensible a acentos; en pruebas se filtra por texto sin tildes (ej. la sigla).
- **Evitar / mejora futura:** si se necesita búsqueda insensible a acentos,
  registrar una función de normalización en la conexión SQLite (o guardar una
  columna "nombre_normalizado" sin tildes) y filtrar sobre ella.

## L-005 · La BD de pruebas es de sesión: usar nombres únicos en fixtures
- **Síntoma:** al añadir `test_recetas.py`, los fixtures que creaban entidades
  con nombre fijo (materia "RCT1", reactivo "EDTA receta") fallaban con
  `KeyError: 'id'` a partir del segundo test que los usaba.
- **Causa:** `conftest.py` crea la BD temporal una sola vez por **sesión**
  (`scope="session"`); los datos persisten entre tests. El segundo `POST` con el
  mismo nombre devuelve 409 (sin `id`), no 201.
- **Solución:** en fixtures que insertan datos de apoyo reutilizables, generar
  nombres únicos por test (`uuid.uuid4().hex[:8]`) y evitar aserciones atadas a
  un nombre fijo.
- **Evitar:** no asumir BD limpia entre tests; o se usan nombres únicos, o se
  cambia el scope del fixture de BD a "function" (más lento).
