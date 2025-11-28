/**
 * Script para copiar los CSVs de UPME a la carpeta public
 * Ejecutar antes del build o en desarrollo
 */
import { cpSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const sourceDir = join(__dirname, '../../data/extraction/scrapers/proyeccion/processed');
const targetDir = join(__dirname, '../public/data/extraction/scrapers/proyeccion/processed');

try {
  // Crear directorio destino si no existe
  mkdirSync(targetDir, { recursive: true });
  
  // Copiar archivos
  cpSync(sourceDir, targetDir, { recursive: true, force: true });
  console.log('✅ CSVs copiados exitosamente a public/data');
} catch (error) {
  console.error('❌ Error copiando CSVs:', error.message);
  process.exit(1);
}

