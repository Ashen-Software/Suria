/**
 * Script para copiar los CSVs de UPME a la carpeta public
 * Ejecutar antes del build o en desarrollo
 */
import { cpSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Buscar datos en múltiples ubicaciones (local y Docker)
const possibleSourceDirs = [
  join(__dirname, '../../data/extraction/scrapers/proyeccion/processed'), // Local: desde frontend/scripts/
  join(__dirname, '../../../data/extraction/scrapers/proyeccion/processed'), // Docker: desde /app/scripts/
  join(process.cwd(), 'data/extraction/scrapers/proyeccion/processed'), // Desde el working directory
  join(__dirname, '../data/extraction/scrapers/proyeccion/processed'), // Docker: desde /app/data/
];

const targetDir = join(__dirname, '../public/data/extraction/scrapers/proyeccion/processed');

// Encontrar el directorio fuente que existe
let sourceDir = null;
for (const dir of possibleSourceDirs) {
  if (existsSync(dir)) {
    sourceDir = dir;
    break;
  }
}

try {
  // Verificar si encontramos un directorio fuente
  if (!sourceDir) {
    console.warn('⚠️  Directorio fuente no encontrado en ninguna ubicación esperada:');
    possibleSourceDirs.forEach(dir => console.warn(`   - ${dir}`));
    console.warn('⚠️  Los datos de UPME no estarán disponibles en el build.');
    console.warn('⚠️  Asegúrate de ejecutar el normalizador antes del build.');
    // Crear el directorio destino vacío para evitar errores
    mkdirSync(targetDir, { recursive: true });
    process.exit(0);
  }
  
  console.log(`📁 Usando directorio fuente: ${sourceDir}`);

  // Crear directorio destino si no existe
  mkdirSync(targetDir, { recursive: true });
  
  // Copiar archivos
  cpSync(sourceDir, targetDir, { recursive: true, force: true });
  console.log('✅ CSVs copiados exitosamente a public/data');
} catch (error) {
  console.error('❌ Error copiando CSVs:', error.message);
  // No hacer exit(1) para permitir que el build continúe
  // Los datos simplemente no estarán disponibles
  console.warn('⚠️  Continuando el build sin datos de UPME...');
}

