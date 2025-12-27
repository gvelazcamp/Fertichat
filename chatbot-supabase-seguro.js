// ====================================
// CONEXIÓN A SUPABASE PARA CHATBOT (SEGURO)
// ====================================

// 1. INSTALACIÓN
// npm install @supabase/supabase-js dotenv

// 2. CARGAR VARIABLES DE ENTORNO
require('dotenv').config();

// 3. IMPORTAR SUPABASE
const { createClient } = require('@supabase/supabase-js');

// 4. CONFIGURACIÓN (desde variables de entorno)
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

// Validar que existan las credenciales
if (!supabaseUrl || !supabaseKey) {
  throw new Error('❌ ERROR: Falta SUPABASE_URL o SUPABASE_ANON_KEY en el archivo .env');
}

// Crear cliente de Supabase
const supabase = createClient(supabaseUrl, supabaseKey);

console.log('✅ Conexión a Supabase establecida correctamente');

// ====================================
// FUNCIONES PARA CHATBOT
// ====================================

// Guardar mensaje en la conversación
async function guardarMensaje(userId, mensaje, esBot = false) {
  try {
    const { data, error } = await supabase
      .from('mensajes')
      .insert([
        {
          user_id: userId,
          mensaje: mensaje,
          es_bot: esBot,
          timestamp: new Date().toISOString()
        }
      ]);

    if (error) throw error;
    console.log('✅ Mensaje guardado');
    return data;
  } catch (error) {
    console.error('❌ Error al guardar mensaje:', error.message);
    return null;
  }
}

// Obtener historial de conversación
async function obtenerHistorial(userId, limite = 50) {
  try {
    const { data, error } = await supabase
      .from('mensajes')
      .select('*')
      .eq('user_id', userId)
      .order('timestamp', { ascending: false })
      .limit(limite);

    if (error) throw error;
    return data;
  } catch (error) {
    console.error('❌ Error al obtener historial:', error.message);
    return [];
  }
}

// Crear o actualizar usuario
async function gestionarUsuario(userId, nombre, datos = {}) {
  try {
    const { data, error } = await supabase
      .from('usuarios')
      .upsert([
        {
          id: userId,
          nombre: nombre,
          ultimo_acceso: new Date().toISOString(),
          ...datos
        }
      ]);

    if (error) throw error;
    console.log('✅ Usuario gestionado');
    return data;
  } catch (error) {
    console.error('❌ Error al gestionar usuario:', error.message);
    return null;
  }
}

// Guardar contexto de la conversación
async function guardarContexto(userId, contexto) {
  try {
    const { data, error } = await supabase
      .from('contextos')
      .upsert([
        {
          user_id: userId,
          contexto: contexto,
          actualizado: new Date().toISOString()
        }
      ]);

    if (error) throw error;
    return data;
  } catch (error) {
    console.error('❌ Error al guardar contexto:', error.message);
    return null;
  }
}

// Obtener contexto de la conversación
async function obtenerContexto(userId) {
  try {
    const { data, error } = await supabase
      .from('contextos')
      .select('contexto')
      .eq('user_id', userId)
      .single();

    if (error) throw error;
    return data?.contexto || null;
  } catch (error) {
    console.error('❌ Error al obtener contexto:', error.message);
    return null;
  }
}

// Búsqueda en base de conocimiento
async function buscarEnBaseDatos(query) {
  try {
    const { data, error } = await supabase
      .from('conocimiento')
      .select('*')
      .textSearch('contenido', query);

    if (error) throw error;
    return data;
  } catch (error) {
    console.error('❌ Error en búsqueda:', error.message);
    return [];
  }
}

// Eliminar historial de un usuario
async function eliminarHistorial(userId) {
  try {
    const { error } = await supabase
      .from('mensajes')
      .delete()
      .eq('user_id', userId);

    if (error) throw error;
    console.log(`✅ Historial eliminado para usuario ${userId}`);
    return true;
  } catch (error) {
    console.error('❌ Error al eliminar historial:', error.message);
    return false;
  }
}

// ====================================
// EJEMPLO DE USO
// ====================================

async function ejemploUso() {
  console.log('\n🤖 Iniciando ejemplo de uso...\n');
  
  const userId = 'user_' + Date.now();
  
  // 1. Registrar usuario
  console.log('1️⃣ Registrando usuario...');
  await gestionarUsuario(userId, 'Usuario Demo', { 
    email: 'demo@example.com' 
  });
  
  // 2. Guardar mensaje del usuario
  console.log('2️⃣ Guardando mensajes...');
  await guardarMensaje(userId, '¿Cuál es el horario de atención?', false);
  
  // 3. Guardar respuesta del bot
  await guardarMensaje(userId, 'Nuestro horario es de 9am a 6pm', true);
  
  // 4. Obtener historial
  console.log('3️⃣ Obteniendo historial...');
  const historial = await obtenerHistorial(userId, 10);
  console.log('📝 Historial:', historial);
  
  // 5. Guardar contexto
  console.log('4️⃣ Guardando contexto...');
  await guardarContexto(userId, { 
    tema: 'horarios', 
    intención: 'consulta' 
  });
  
  // 6. Recuperar contexto
  console.log('5️⃣ Recuperando contexto...');
  const contexto = await obtenerContexto(userId);
  console.log('📌 Contexto:', contexto);
  
  console.log('\n✨ Ejemplo completado!\n');
}

// Descomentar para probar:
// ejemploUso();

// ====================================
// EXPORTAR FUNCIONES
// ====================================

module.exports = {
  supabase,
  guardarMensaje,
  obtenerHistorial,
  gestionarUsuario,
  guardarContexto,
  obtenerContexto,
  buscarEnBaseDatos,
  eliminarHistorial
};
