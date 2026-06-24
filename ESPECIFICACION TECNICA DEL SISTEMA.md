# Especificación Técnica y de Negocio: Sistema de Control de Insumos (Laboratorio de Química - UAJMS)

Este documento centraliza todas las decisiones de diseño, reglas de negocio y estructuras lógicas acordadas para el desarrollo del sistema local de gestión de insumos y materiales del Laboratorio de Química. Está diseñado para servir como contexto inmediato y completo para agentes de desarrollo y programadores.

---

## 1. Visión General del Sistema
El sistema tiene como objetivo digitalizar la logística física del laboratorio, automatizando el control de reactivos y materiales mediante un concepto centralizador denominado **"Carrito de Insumos"**. Reemplaza el seguimiento miligramo a miligramo en tiempo real por un control de carga por bloques, alineado con los horarios académicos y las **Recetas Maestras** (plantillas estandarizadas de prácticas).

### Características de Despliegue e Interfaz
* **Despliegue Local (LAN):** El sistema se alojará en un servidor local dentro de la red del laboratorio, operando sin dependencia de internet externo. Contará con una IP estática para garantizar un acceso permanente.
* **Acceso Móvil (Mobile-First):** La administradora operará el sistema principalmente desde su dispositivo móvil mientras se desplaza por los ambientes. Se estructurará como una **PWA (Progressive Web App)** para permitir su instalación en la pantalla de inicio del dispositivo, eliminando barras de navegación innecesarias.
* **Acceso Ágil:** Se implementarán códigos QR físicos en los laboratorios que apunten directamente a la dirección IP local del servidor para facilitar la conexión instantánea del dispositivo móvil.

---

## 2. Reglas de Negocio Críticas

### A. Centralización por "Carrito de Insumos"
Los reactivos y materiales no se despachan de forma individual y aislada en el sistema. Se agrupan lógicamente en un **"Carrito"** asignado a un Docente, Materia, Grupo y Ambiente físico específico para una jornada o práctica determinada. Cada carrito se **arma de forma predeterminada a partir de una Receta Maestra** asociada a la práctica.

### B. Separación Estricta de Insumos
El sistema procesa los elementos del carrito mediante dos lógicas de inventario completamente diferenciadas debido a su naturaleza física:
1.  **Módulo de Reactivos (Consumibles):**
    * Se miden por una cantidad numérica y un descriptor de **concentración/unidad** unificado (ej: cantidad `70` con descriptor `1M / mL`).
    * **SIN gestión de stock:** No se controla inventario de reactivos porque **no es posible determinar con exactitud el total disponible en almacén**. La tabla `reactivos` es solo un **catálogo de nombres** (sin `stock_actual` ni `stock_minimo`). En el carrito, el reactivo es una **lista de preparación** (qué preparar y cuánto por grupo): el sistema **no descuenta de ningún stock** ni emite alertas de reposición.
2.  **Módulo de Materiales (Retornables/Activos fijos):**
    * Se miden por unidades y capacidad de equipamiento (ej: 5 probetas de 100 mL, 60 tubos de ensayo).
    * **Lógica de control:** No se descuentan del stock al iniciar la clase; incrementan la `cantidad_en_uso` del material. Al finalizar la práctica, el sistema exige una **Conciliación de Materiales** (unidades entregadas vs. unidades devueltas).

### C. Unicidad del Carrito y Concurrencia de Docentes
* El sistema soporta el funcionamiento simultáneo de 2 o 3 docentes en diferentes ambientes físicos (ej: laboratorio INA014, LAB QMC) al mismo tiempo.
* **Asincronía de Avance:** El sistema no fuerza a que todos los docentes vayan al mismo ritmo académico. El armado del carrito es independiente; un docente puede solicitar la "Práctica 11" mientras otro en el mismo horario solicita la "Práctica 8". El sistema cargará la receta correspondiente de forma flexible.
* **Regla de Unicidad (PROHIBICIÓN):** Está **prohibido que existan dos carritos con la misma Materia + la misma Práctica + en el mismo horario**. Es decir, dos docentes no pueden dar la misma materia ejecutando la misma práctica en el mismo bloque horario.
* **Caso Permitido:** Si dos docentes comparten la **misma materia** y el **mismo horario** pero realizan **prácticas diferentes**, sí se permite: son carritos distintos e independientes. La distinción se da por la práctica.
* **Reutilización por Horario:** Una misma materia y/o una misma práctica pueden repetirse en **distintos horarios** (diferentes bloques o fechas) sin restricción, generando carritos independientes.

### D. Horario y Ambiente Dinámicos
* El horario y el ambiente asignados a un docente son **referenciales y pueden variar**. Algunos docentes cambian el bloque horario o el ambiente que ocupan según la jornada.
* Por ello, el horario y el ambiente **reales** se capturan a nivel de **carrito** en el momento del armado, pudiendo diferir del valor planificado en `horarios_semestre`. El catálogo de horarios sirve como referencia/sugerencia, no como dato rígido.

### E. Plantilla de Materiales Editable
* Al armar el carrito desde una Receta Maestra, las líneas de materiales (y reactivos) se **copian** al detalle del carrito.
* Este detalle es **editable**: la administradora puede **añadir elementos extra** (2 o 3 materiales adicionales que un docente necesite puntualmente) o ajustar cantidades, sin alterar la Receta Maestra original. Las líneas añadidas manualmente se marcan como `es_extra`.

### F. Gestión de Prácticas Incompletas ("Check a Medias")
Si un grupo no logra concluir la práctica en el horario establecido:
1.  La administradora registra un **"Check a medias"** (Práctica Incompleta).
2.  El carrito pasa al estado **"En Custodia"**.
3.  **Congelamiento de Stock:** Los reactivos ya preparados permanecen lógicamente atrapados en ese carrito para evitar que se vuelvan a preparar y gastar doble stock la siguiente semana. Los materiales quedan vinculados exclusivamente a ese docente y grupo.
4.  La próxima clase, el sistema bloquea la creación de un nuevo requerimiento para ese mismo docente/grupo y emite una alerta para entregar el carrito custodiado.

### G. Flujo de Control Legal e Histórico (Sin Firma Digital)
Para simplificar el desarrollo y mantener los procesos institucionales vigentes:
* La firma física de responsabilidad seguirá existiendo exclusivamente en las planillas de papel.
* El sistema digital omitirá la **firma electrónica de las acciones**. En su lugar, registrará automáticamente una marca de tiempo (**Timestamp**) inmutable con la fecha y hora exacta en que la administradora ejecuta acciones críticas (Creación, Custodia, Cierre). Todo movimiento de inventario de **materiales** se registra en el **Kardex** (`movimientos_inventario`).
* **Autenticación de acceso:** el sistema **sí** exige un **login** para entrar (control de acceso, no firma de acciones). Inicialmente existe un único usuario **administrador**; el modelo (`usuarios`, con campo `rol`) queda preparado para crear nuevos usuarios y roles a futuro. Las contraseñas se almacenan con hash (pbkdf2), nunca en claro.

### H. Reactivos sin inventario
Recordatorio transversal: **en todo el sistema, los reactivos no llevan control de stock** (ver Regla 2.B.1). Solo los **materiales** tienen inventario, conciliación y Kardex.

---

## 3. Ciclo de Vida del Carrito (Estados del Sistema)

El flujo de control de un carrito se rige bajo la siguiente secuencia lógica de estados:

1.  **En Preparación:** Estado inicial donde la administradora selecciona la "Receta Maestra" (plantilla de la práctica) y arma el carrito. Puede editar el detalle (añadir extras / ajustar cantidades) antes de confirmar.
2.  **Activo / Entregado:** El carrito ingresa al laboratorio físico. Los reactivos se descuentan del stock general y los materiales incrementan su `cantidad_en_uso`. El dashboard muestra el carrito bajo el ambiente correspondiente.
3.  **En Custodia (Estado Opcional de Pausa):** Activado ante un "check a medias". Retiene los insumos de forma lógica y bloquea al docente/grupo hasta la siguiente sesión académica.
4.  **Próximo a Cerrarse:** Bandeja de auditoría pendiente. **Esta transición es MANUAL, decidida por la administradora — NO se dispara por el reloj/horario.** El motivo es que algunos docentes continúan con la siguiente clase de forma encadenada, por lo que la finalización real no coincide con la hora teórica del bloque. La administradora mueve el carrito a esta bandeja cuando constata que la jornada del docente terminó.
5.  **Depurado / Cerrado:** Estado final. Tras validar que los materiales retornaron completos (o registrar mermas por rotura) el carrito se cierra de forma definitiva.

---

## 4. Arquitectura de la Base de Datos (Estructura Relacional)

Diseñada para entornos ligeros y eficientes en redes locales (Recomendado: SQLite). Se introduce normalización de catálogos (docentes, materias, ambientes), inventario maestro (stock), Recetas Maestras reutilizables y un Kardex de movimientos. Las fechas se almacenan en formato ISO-8601 (`YYYY-MM-DD HH:MM:SS`).

```sql
PRAGMA foreign_keys = ON;

-- ============================================================
-- SEGURIDAD / USUARIOS (autenticación de acceso, Regla 2.G)
-- ============================================================
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario TEXT NOT NULL UNIQUE,        -- login
    nombre_completo TEXT,
    password_hash TEXT NOT NULL,                -- pbkdf2; nunca la clave en claro
    rol TEXT NOT NULL DEFAULT 'administrador'
        CHECK (rol IN ('administrador')),       -- extensible a futuro
    activo INTEGER NOT NULL DEFAULT 1,
    timestamp_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CATÁLOGOS NORMALIZADOS
-- ============================================================

CREATE TABLE docentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE          -- Ej: Condori, Irusta
);

CREATE TABLE materias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sigla TEXT NOT NULL,                 -- Ej: QMC021, BAS100
    nombre TEXT NOT NULL,                -- Ej: Química Orgánica I
    carrera TEXT NOT NULL,               -- Ej: ING. QUÍMICA, FARMACIA
    UNIQUE(sigla, nombre)
);

CREATE TABLE ambientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE          -- Ej: INA014, LAB QMC
);

-- 1. Catálogo Base de Horarios y Distribución Académica (REFERENCIAL)
-- El horario/ambiente real puede variar y se captura en el carrito (Regla 2.D).
CREATE TABLE horarios_semestre (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia_id INTEGER NOT NULL,
    docente_id INTEGER NOT NULL,
    ambiente_id INTEGER,                 -- Ambiente sugerido/habitual
    grupo_designado TEXT NOT NULL,       -- Ej: P1(G), P2(G), Grupo 12
    dia_semana TEXT,                     -- Ej: Lun, Mar, Mie
    hora_inicio TEXT,                    -- Ej: '14:00'
    hora_fin TEXT,                       -- Ej: '16:00' (referencial, NO cierra el carrito)
    FOREIGN KEY(materia_id) REFERENCES materias(id),
    FOREIGN KEY(docente_id) REFERENCES docentes(id),
    FOREIGN KEY(ambiente_id) REFERENCES ambientes(id)
);

-- ============================================================
-- INVENTARIO MAESTRO (STOCK)
-- ============================================================

-- Catálogo de Reactivos (Consumibles) — SIN stock (Regla 2.B.1)
CREATE TABLE reactivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT,                         -- Ej: M.F, K.P
    nombre TEXT NOT NULL,                -- Ej: EDTA, H2SO4
    unidad_base TEXT                     -- Ej: mL, g (referencial, no stock)
);

-- Catálogo + stock de Materiales (Retornables / Activos fijos)
CREATE TABLE materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT,
    nombre TEXT NOT NULL,                -- Ej: Buretas, Pipetas Graduadas
    capacidad TEXT,                      -- Ej: 10/5 mL, 100 mL
    cantidad_total INTEGER NOT NULL DEFAULT 0,  -- Patrimonio total del laboratorio
    cantidad_en_uso INTEGER NOT NULL DEFAULT 0  -- Unidades actualmente en carritos activos
);

-- ============================================================
-- RECETAS MAESTRAS (PLANTILLAS REUTILIZABLES)
-- ============================================================

CREATE TABLE recetas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia_id INTEGER NOT NULL,
    nombre_practica TEXT NOT NULL,       -- Ej: Complexometría #6
    descripcion TEXT,
    activa INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(materia_id) REFERENCES materias(id),
    UNIQUE(materia_id, nombre_practica)
);

CREATE TABLE receta_detalle_reactivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receta_id INTEGER NOT NULL,
    reactivo_id INTEGER NOT NULL,
    concentracion_unidad TEXT,           -- Casilla unificada. Ej: '0,01M / mL', '1M / g'
    cantidad_por_grupo REAL NOT NULL,
    FOREIGN KEY(receta_id) REFERENCES recetas(id) ON DELETE CASCADE,
    FOREIGN KEY(reactivo_id) REFERENCES reactivos(id)
);

CREATE TABLE receta_detalle_materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receta_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    cantidad_por_grupo INTEGER NOT NULL,
    observaciones TEXT,                  -- Ej: "grandes", "plastico"
    FOREIGN KEY(receta_id) REFERENCES recetas(id) ON DELETE CASCADE,
    FOREIGN KEY(material_id) REFERENCES materiales(id)
);

-- ============================================================
-- CARRITO (REQUERIMIENTO INSTANCIADO)
-- ============================================================

-- 2. Entidad Central del Requerimiento (Cabecera del Carrito)
CREATE TABLE carritos_cabecera (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    docente_id INTEGER NOT NULL,
    materia_id INTEGER NOT NULL,
    receta_id INTEGER,                       -- Receta Maestra origen (puede ser NULL si fue manual)
    nombre_numero_practica TEXT NOT NULL,    -- Ej: Complexometría #6
    fecha_realizacion TEXT NOT NULL,         -- Fecha programada de la clase (YYYY-MM-DD)
    -- Horario y ambiente REALES (dinámicos, Regla 2.D):
    ambiente_id INTEGER,
    hora_inicio TEXT,                        -- Bloque real usado ese día
    hora_fin TEXT,
    numero_pedido INTEGER,
    numero_grupos TEXT,                      -- Grupos que usarán el carrito (ej: "1 y 3")
    codigo_lab_qmc TEXT,
    estado_carrito TEXT NOT NULL DEFAULT 'Preparacion'
        CHECK (estado_carrito IN ('Preparacion','Activo','Custodia','Proximo_Cierre','Cerrado')),
    timestamp_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    timestamp_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(docente_id) REFERENCES docentes(id),
    FOREIGN KEY(materia_id) REFERENCES materias(id),
    FOREIGN KEY(receta_id) REFERENCES recetas(id),
    FOREIGN KEY(ambiente_id) REFERENCES ambientes(id)
);

-- REGLA DE UNICIDAD (Regla 2.C): prohíbe dos carritos con la misma
-- Materia + Práctica + mismo bloque horario en la misma fecha.
-- Prácticas diferentes en el mismo horario SÍ se permiten (clave distinta).
-- Solo aplica a carritos no cerrados.
CREATE UNIQUE INDEX idx_carrito_unico_practica
ON carritos_cabecera (materia_id, nombre_numero_practica, fecha_realizacion, hora_inicio)
WHERE estado_carrito <> 'Cerrado';

-- 3. Detalle de Materiales del Carrito (Lógica de Activos / Retornables) — EDITABLE
CREATE TABLE carrito_detalle_materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrito_id INTEGER NOT NULL,
    material_id INTEGER,                 -- FK al catálogo (NULL solo si es ítem libre excepcional)
    nombre_material TEXT NOT NULL,       -- Copia para histórico. Ej: Buretas, Pipetas
    capacidad TEXT,                      -- Ej: 10/5 mL, 100 mL
    cantidad_entregada INTEGER NOT NULL,
    cantidad_devuelta INTEGER,           -- Se llena en la auditoría de cierre
    es_extra INTEGER NOT NULL DEFAULT 0, -- 1 = añadido manualmente fuera de la receta (Regla 2.E)
    observaciones TEXT,
    FOREIGN KEY(carrito_id) REFERENCES carritos_cabecera(id) ON DELETE CASCADE,
    FOREIGN KEY(material_id) REFERENCES materiales(id)
);

-- 4. Detalle de Reactivos del Carrito (Lógica de Consumibles) — EDITABLE
CREATE TABLE carrito_detalle_reactivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrito_id INTEGER NOT NULL,
    reactivo_id INTEGER,
    nombre_reactivo TEXT NOT NULL,       -- Copia para histórico. Ej: EDTA, H2SO4
    concentracion_unidad TEXT,           -- Casilla unificada. Ej: '0,01M / mL', '1M / g'
    cantidad_por_grupo REAL NOT NULL,
    cantidad_total REAL NOT NULL,        -- Calculado automáticamente por el sistema
    es_extra INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(carrito_id) REFERENCES carritos_cabecera(id) ON DELETE CASCADE,
    FOREIGN KEY(reactivo_id) REFERENCES reactivos(id)
);

-- 5. Registro Histórico de Material Roto o Perdido (Mermas Auditadas)
CREATE TABLE registro_material_roto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrito_id INTEGER NOT NULL,
    detalle_material_id INTEGER,         -- Línea exacta del detalle que generó la merma
    fecha_reporte TEXT NOT NULL,
    codigo_material TEXT,
    tipo_material TEXT NOT NULL,
    docente_responsable TEXT NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    observaciones_rotura TEXT,
    FOREIGN KEY(carrito_id) REFERENCES carritos_cabecera(id),
    FOREIGN KEY(detalle_material_id) REFERENCES carrito_detalle_materiales(id)
);

-- 6. Kardex / Movimientos de Inventario (trazabilidad inmutable, Regla 2.G)
CREATE TABLE movimientos_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrito_id INTEGER,
    tipo_insumo TEXT NOT NULL CHECK (tipo_insumo IN ('reactivo','material')),
    insumo_id INTEGER NOT NULL,          -- reactivos.id o materiales.id según tipo_insumo
    tipo_movimiento TEXT NOT NULL        -- 'salida_consumo','entrada_uso','retorno','merma','ajuste'
        CHECK (tipo_movimiento IN ('salida_consumo','entrada_uso','retorno','merma','ajuste')),
    cantidad REAL NOT NULL,
    timestamp_movimiento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(carrito_id) REFERENCES carritos_cabecera(id)
);

-- Índices de apoyo para el dashboard y bloqueos por estado/ambiente
CREATE INDEX idx_carritos_estado   ON carritos_cabecera(estado_carrito);
CREATE INDEX idx_carritos_fecha     ON carritos_cabecera(fecha_realizacion);
CREATE INDEX idx_carritos_docente   ON carritos_cabecera(docente_id, estado_carrito);
```

### Notas de implementación clave
* **Armado del carrito:** al elegir una `receta`, el backend **copia** sus líneas a `carrito_detalle_reactivos` / `carrito_detalle_materiales`. A partir de ahí el detalle es independiente y editable (extras con `es_extra = 1`).
* **Cálculo de `cantidad_total` (reactivos):** se calcula como `cantidad_por_grupo × (nº de grupos del carrito)` en el momento del armado. Es la **cantidad a preparar**, NO un descuento de stock (los reactivos no tienen inventario).
* **Paso a "Activo":** solo afecta a **materiales** → por cada material, `materiales.cantidad_en_uso += cantidad_entregada` + registro en `movimientos_inventario` (`entrada_uso`). Los reactivos no generan ningún movimiento de stock.
* **Cierre (paso a "Cerrado"):** se concilia `cantidad_devuelta`; los materiales devueltos hacen `cantidad_en_uso -= cantidad_devuelta` (`retorno`); el faltante se registra en `registro_material_roto` (`merma`).
* **Regla de unicidad:** el índice `idx_carrito_unico_practica` impide a nivel de base de datos crear dos carritos con misma materia + práctica + bloque horario en una misma fecha (ver Regla 2.C).
* **Cierre manual:** no existe job/cron de cierre por horario. El estado `Proximo_Cierre` lo establece la administradora (ver Regla/estado 3.4 y 2.D).
