-- ====================================
-- ESTRUCTURA DE TABLAS PARA CHATBOT EN SUPABASE
-- ====================================

-- Ejecuta estos comandos en el SQL Editor de Supabase
-- (Panel de Supabase > SQL Editor > New Query)

-- TABLA: usuarios
-- Almacena información de los usuarios del chatbot
CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    email TEXT,
    telefono TEXT,
    ultimo_acceso TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- TABLA: mensajes
-- Almacena todos los mensajes de las conversaciones
CREATE TABLE IF NOT EXISTS mensajes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    mensaje TEXT NOT NULL,
    es_bot BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para mejorar búsquedas por usuario
CREATE INDEX IF NOT EXISTS idx_mensajes_user_id ON mensajes(user_id);
CREATE INDEX IF NOT EXISTS idx_mensajes_timestamp ON mensajes(timestamp DESC);

-- TABLA: contextos
-- Almacena el contexto de las conversaciones
CREATE TABLE IF NOT EXISTS contextos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    contexto JSONB,
    actualizado TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- TABLA: conocimiento (opcional)
-- Base de conocimiento para el chatbot
CREATE TABLE IF NOT EXISTS conocimiento (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    titulo TEXT,
    contenido TEXT NOT NULL,
    categoria TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice de búsqueda de texto completo
CREATE INDEX IF NOT EXISTS idx_conocimiento_contenido ON conocimiento USING GIN (to_tsvector('spanish', contenido));

-- ====================================
-- POLÍTICAS DE SEGURIDAD (RLS)
-- ====================================

-- Habilitar Row Level Security
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE mensajes ENABLE ROW LEVEL SECURITY;
ALTER TABLE contextos ENABLE ROW LEVEL SECURITY;
ALTER TABLE conocimiento ENABLE ROW LEVEL SECURITY;

-- Políticas para usuarios (permitir todo con anon key)
CREATE POLICY "Permitir todas las operaciones en usuarios" ON usuarios
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Permitir todas las operaciones en mensajes" ON mensajes
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Permitir todas las operaciones en contextos" ON contextos
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Permitir lectura en conocimiento" ON conocimiento
    FOR SELECT USING (true);

CREATE POLICY "Permitir todas las operaciones en conocimiento" ON conocimiento
    FOR ALL USING (true) WITH CHECK (true);

-- ====================================
-- DATOS DE EJEMPLO
-- ====================================

-- Insertar datos de prueba en la tabla de conocimiento
INSERT INTO conocimiento (titulo, contenido, categoria, tags) VALUES
    ('Horarios', 'Nuestro horario de atención es de lunes a viernes de 9:00 AM a 6:00 PM', 'general', ARRAY['horario', 'atención']),
    ('Productos', 'Ofrecemos servicios de consultoría, desarrollo web y aplicaciones móviles', 'servicios', ARRAY['productos', 'servicios']),
    ('Contacto', 'Puedes contactarnos al email info@empresa.com o al teléfono +1-234-567-8900', 'contacto', ARRAY['contacto', 'soporte'])
ON CONFLICT DO NOTHING;

-- ====================================
-- FUNCIONES ÚTILES
-- ====================================

-- Función para limpiar mensajes antiguos (más de 30 días)
CREATE OR REPLACE FUNCTION limpiar_mensajes_antiguos()
RETURNS void AS $$
BEGIN
    DELETE FROM mensajes 
    WHERE timestamp < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Función para obtener estadísticas de uso
CREATE OR REPLACE FUNCTION estadisticas_chatbot()
RETURNS TABLE(
    total_usuarios BIGINT,
    total_mensajes BIGINT,
    mensajes_hoy BIGINT,
    usuarios_activos_hoy BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM usuarios),
        (SELECT COUNT(*) FROM mensajes),
        (SELECT COUNT(*) FROM mensajes WHERE timestamp::date = CURRENT_DATE),
        (SELECT COUNT(DISTINCT user_id) FROM mensajes WHERE timestamp::date = CURRENT_DATE);
END;
$$ LANGUAGE plpgsql;

-- ====================================
-- VISTAS ÚTILES
-- ====================================

-- Vista de conversaciones recientes
CREATE OR REPLACE VIEW conversaciones_recientes AS
SELECT 
    u.id,
    u.nombre,
    COUNT(m.id) as total_mensajes,
    MAX(m.timestamp) as ultimo_mensaje
FROM usuarios u
LEFT JOIN mensajes m ON u.id = m.user_id
GROUP BY u.id, u.nombre
ORDER BY ultimo_mensaje DESC;
