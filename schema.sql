-- ============================================================
-- Sistema de Control de Insumos - Laboratorio de Química (UAJMS)
-- Esquema de Base de Datos (SQLite)
-- Generado a partir de "ESPECIFICACION TECNICA DEL SISTEMA.md"
-- Fechas en formato ISO-8601 (YYYY-MM-DD HH:MM:SS)
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- SEGURIDAD / USUARIOS (autenticación)
-- ============================================================
-- Acceso por login. No reemplaza la firma física en papel ni añade firma
-- digital a las acciones (se mantienen los timestamps inmutables, Regla 2.G):
-- solo controla quién entra al sistema. Diseñado para crecer a más roles.
CREATE TABLE IF NOT EXISTS usuarios (
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

CREATE TABLE IF NOT EXISTS docentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE             -- Ej: Condori, Irusta
);

CREATE TABLE IF NOT EXISTS materias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sigla TEXT NOT NULL,                    -- Ej: QMC021, BAS100
    nombre TEXT NOT NULL,                   -- Ej: Química Orgánica I
    carrera TEXT NOT NULL,                  -- Ej: ING. QUÍMICA, FARMACIA
    UNIQUE(sigla, nombre)
);

CREATE TABLE IF NOT EXISTS ambientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE             -- Ej: INA014, LAB QMC
);

-- Catálogo Base de Horarios y Distribución Académica (REFERENCIAL).
-- El horario/ambiente real puede variar y se captura en el carrito (Regla 2.D).
CREATE TABLE IF NOT EXISTS horarios_semestre (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia_id INTEGER NOT NULL,
    docente_id INTEGER NOT NULL,
    ambiente_id INTEGER,                    -- Ambiente sugerido/habitual
    grupo_designado TEXT NOT NULL,          -- Ej: P1(G), P2(G), Grupo 12
    dia_semana TEXT,                        -- Ej: Lun, Mar, Mie
    hora_inicio TEXT,                       -- Ej: '14:00'
    hora_fin TEXT,                          -- Ej: '16:00' (referencial, NO cierra el carrito)
    FOREIGN KEY(materia_id) REFERENCES materias(id),
    FOREIGN KEY(docente_id) REFERENCES docentes(id),
    FOREIGN KEY(ambiente_id) REFERENCES ambientes(id)
);

-- ============================================================
-- INVENTARIO MAESTRO (STOCK)
-- ============================================================

-- Catálogo de Reactivos (Consumibles).
-- NO se gestiona stock: no se puede determinar el total real en almacén
-- (Regla 2.B). Funciona solo como catálogo de nombres para recetas/carritos;
-- el reactivo en el carrito es una LISTA DE PREPARACIÓN, no un descuento.
CREATE TABLE IF NOT EXISTS reactivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT,                            -- Ej: M.F, K.P
    nombre TEXT NOT NULL,                   -- Ej: EDTA, H2SO4
    unidad_base TEXT                        -- Ej: mL, g (referencial, no stock)
);

-- Catálogo + stock de Materiales (Retornables / Activos fijos)
CREATE TABLE IF NOT EXISTS materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT,
    nombre TEXT NOT NULL,                   -- Ej: Buretas, Pipetas Graduadas
    capacidad TEXT,                         -- Ej: 10/5 mL, 100 mL
    cantidad_total INTEGER NOT NULL DEFAULT 0,   -- Patrimonio total del laboratorio
    cantidad_en_uso INTEGER NOT NULL DEFAULT 0   -- Unidades actualmente en carritos activos
);

-- ============================================================
-- RECETAS MAESTRAS (PLANTILLAS REUTILIZABLES)
-- ============================================================

CREATE TABLE IF NOT EXISTS recetas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia_id INTEGER NOT NULL,
    nombre_practica TEXT NOT NULL,          -- Ej: Complexometría #6
    descripcion TEXT,
    activa INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(materia_id) REFERENCES materias(id),
    UNIQUE(materia_id, nombre_practica)
);

CREATE TABLE IF NOT EXISTS receta_detalle_reactivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receta_id INTEGER NOT NULL,
    reactivo_id INTEGER NOT NULL,
    concentracion_unidad TEXT,              -- Casilla unificada. Ej: '0,01M / mL', '1M / g'
    cantidad_por_grupo REAL NOT NULL,
    FOREIGN KEY(receta_id) REFERENCES recetas(id) ON DELETE CASCADE,
    FOREIGN KEY(reactivo_id) REFERENCES reactivos(id)
);

CREATE TABLE IF NOT EXISTS receta_detalle_materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receta_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    cantidad_por_grupo INTEGER NOT NULL,
    observaciones TEXT,                     -- Ej: "grandes", "plastico"
    FOREIGN KEY(receta_id) REFERENCES recetas(id) ON DELETE CASCADE,
    FOREIGN KEY(material_id) REFERENCES materiales(id)
);

-- ============================================================
-- CARRITO (REQUERIMIENTO INSTANCIADO)
-- ============================================================

-- Entidad Central del Requerimiento (Cabecera del Carrito)
CREATE TABLE IF NOT EXISTS carritos_cabecera (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    docente_id INTEGER NOT NULL,
    materia_id INTEGER NOT NULL,
    receta_id INTEGER,                          -- Receta Maestra origen (NULL si fue manual)
    nombre_numero_practica TEXT NOT NULL,       -- Ej: Complexometría #6
    fecha_realizacion TEXT NOT NULL,            -- Fecha programada (YYYY-MM-DD)
    -- Horario y ambiente REALES (dinámicos, Regla 2.D):
    ambiente_id INTEGER,
    hora_inicio TEXT,                           -- Bloque real usado ese día
    hora_fin TEXT,
    numero_pedido INTEGER,
    numero_grupos TEXT,                         -- Grupos que usarán el carrito (ej: "1 y 3")
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
CREATE UNIQUE INDEX IF NOT EXISTS idx_carrito_unico_practica
ON carritos_cabecera (materia_id, nombre_numero_practica, fecha_realizacion, hora_inicio)
WHERE estado_carrito <> 'Cerrado';

-- Detalle de Materiales del Carrito (Lógica de Activos / Retornables) — EDITABLE
CREATE TABLE IF NOT EXISTS carrito_detalle_materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrito_id INTEGER NOT NULL,
    material_id INTEGER,                    -- FK al catálogo (NULL solo si es ítem libre excepcional)
    nombre_material TEXT NOT NULL,          -- Copia para histórico. Ej: Buretas, Pipetas
    capacidad TEXT,                         -- Ej: 10/5 mL, 100 mL
    cantidad_entregada INTEGER NOT NULL,
    cantidad_devuelta INTEGER,              -- Se llena en la auditoría de cierre
    es_extra INTEGER NOT NULL DEFAULT 0,    -- 1 = añadido manualmente fuera de la receta (Regla 2.E)
    observaciones TEXT,
    FOREIGN KEY(carrito_id) REFERENCES carritos_cabecera(id) ON DELETE CASCADE,
    FOREIGN KEY(material_id) REFERENCES materiales(id)
);

-- Detalle de Reactivos del Carrito (Lógica de Consumibles) — EDITABLE
CREATE TABLE IF NOT EXISTS carrito_detalle_reactivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrito_id INTEGER NOT NULL,
    reactivo_id INTEGER,
    nombre_reactivo TEXT NOT NULL,          -- Copia para histórico. Ej: EDTA, H2SO4
    concentracion_unidad TEXT,              -- Casilla unificada. Ej: '0,01M / mL', '1M / g'
    cantidad_por_grupo REAL NOT NULL,
    cantidad_total REAL NOT NULL,           -- Calculado automáticamente por el sistema
    es_extra INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(carrito_id) REFERENCES carritos_cabecera(id) ON DELETE CASCADE,
    FOREIGN KEY(reactivo_id) REFERENCES reactivos(id)
);

-- Registro Histórico de Material Roto o Perdido (Mermas Auditadas)
CREATE TABLE IF NOT EXISTS registro_material_roto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrito_id INTEGER NOT NULL,
    detalle_material_id INTEGER,            -- Línea exacta del detalle que generó la merma
    fecha_reporte TEXT NOT NULL,
    codigo_material TEXT,
    tipo_material TEXT NOT NULL,
    docente_responsable TEXT NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    observaciones_rotura TEXT,
    FOREIGN KEY(carrito_id) REFERENCES carritos_cabecera(id),
    FOREIGN KEY(detalle_material_id) REFERENCES carrito_detalle_materiales(id)
);

-- Kardex / Movimientos de Inventario (trazabilidad inmutable, Regla 2.G)
CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrito_id INTEGER,
    tipo_insumo TEXT NOT NULL CHECK (tipo_insumo IN ('reactivo','material')),
    insumo_id INTEGER NOT NULL,             -- reactivos.id o materiales.id según tipo_insumo
    tipo_movimiento TEXT NOT NULL
        CHECK (tipo_movimiento IN ('salida_consumo','entrada_uso','retorno','merma','ajuste')),
    cantidad REAL NOT NULL,
    timestamp_movimiento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(carrito_id) REFERENCES carritos_cabecera(id)
);

-- ============================================================
-- ÍNDICES DE APOYO (dashboard / bloqueos por estado)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_carritos_estado  ON carritos_cabecera(estado_carrito);
CREATE INDEX IF NOT EXISTS idx_carritos_fecha    ON carritos_cabecera(fecha_realizacion);
CREATE INDEX IF NOT EXISTS idx_carritos_docente  ON carritos_cabecera(docente_id, estado_carrito);

-- ============================================================
-- TRIGGER: mantener timestamp_actualizacion en cada UPDATE
-- ============================================================
CREATE TRIGGER IF NOT EXISTS trg_carritos_touch
AFTER UPDATE ON carritos_cabecera
FOR EACH ROW
BEGIN
    UPDATE carritos_cabecera
       SET timestamp_actualizacion = CURRENT_TIMESTAMP
     WHERE id = OLD.id;
END;
