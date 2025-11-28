import type { EnergiaElectricaRecord, PotenciaMaximaRecord, CapacidadInstaladaRecord, GasNaturalRecord } from '@/types/upme.types';

// Rutas hardcodeadas a los CSVs procesados
// Nota: En producción, estos deberían venir de un endpoint API
// Los archivos se copian a public/data durante el build
const BASE_DATA_PATH = '/data/extraction/scrapers/proyeccion/processed';

export const UPME_DATA_PATHS = {
  energia: [
    `${BASE_DATA_PATH}/energia-electrica/Anexo_proyeccion_demanda_2025_2039_verJul2025_energia_normalized.csv`,
    `${BASE_DATA_PATH}/energia-electrica/Anexo_proyeccion_demanda_2024_2038_v2_Jul2024_energia_normalized.csv`,
    `${BASE_DATA_PATH}/energia-electrica/Anexo_proyeccion_demanda_EE_2023_2037_energia_normalized.csv`,
  ],
  potencia: [
    `${BASE_DATA_PATH}/potencia-maxima/Anexo_proyeccion_demanda_2025_2039_verJul2025_potencia_normalized.csv`,
    `${BASE_DATA_PATH}/potencia-maxima/Anexo_proyeccion_demanda_2024_2038_v2_Jul2024_potencia_normalized.csv`,
    `${BASE_DATA_PATH}/potencia-maxima/Anexo_proyeccion_demanda_EE_2023_2037_potencia_normalized.csv`,
  ],
  capacidad: [
    `${BASE_DATA_PATH}/capacidad-instalada/Anexo_proyeccion_demanda_2025_2039_verJul2025_capacidad_normalized.csv`,
    `${BASE_DATA_PATH}/capacidad-instalada/Anexo_proyeccion_demanda_2024_2038_v2_Jul2024_capacidad_normalized.csv`,
    `${BASE_DATA_PATH}/capacidad-instalada/Anexo_proyeccion_demanda_EE_2023_2037_capacidad_normalized.csv`,
  ],
  gas: [
    `${BASE_DATA_PATH}/gas-natural/gas_natural_consolidado_normalized.csv`,
  ],
} as const;

/**
 * Parsea un CSV y retorna los registros
 * Maneja valores entre comillas y comas dentro de campos
 */
async function parseCSV<T>(url: string): Promise<T[]> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}: ${response.statusText}`);
    }
    const text = await response.text();
    const lines = text.split('\n').filter(line => line.trim());
    
    if (lines.length < 2) {
      return [];
    }

    // Parsear headers
    const headerLine = lines[0];
    const headers: string[] = [];
    let currentHeader = '';
    let inQuotes = false;
    
    for (let i = 0; i < headerLine.length; i++) {
      const char = headerLine[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        headers.push(currentHeader.trim());
        currentHeader = '';
      } else {
        currentHeader += char;
      }
    }
    headers.push(currentHeader.trim());

    const records: T[] = [];

    // Parsear cada línea
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i];
      const values: string[] = [];
      let currentValue = '';
      let inQuotes = false;
      
      for (let j = 0; j < line.length; j++) {
        const char = line[j];
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          values.push(currentValue.trim());
          currentValue = '';
        } else {
          currentValue += char;
        }
      }
      values.push(currentValue.trim());

      if (values.length !== headers.length) continue;

      const record: any = {};
      headers.forEach((header, index) => {
        let value: any = values[index];
        
        // Remover comillas si existen
        if (value.startsWith('"') && value.endsWith('"')) {
          value = value.slice(1, -1);
        }
        
        // Convertir valores numéricos
        if (header === 'valor') {
          value = parseFloat(value) || 0;
        } else if (value === '' || value === 'null' || value === 'NULL') {
          value = null;
        }
        
        record[header] = value;
      });
      
      records.push(record as T);
    }

    return records;
  } catch (error) {
    console.error(`Error parsing CSV from ${url}:`, error);
    return [];
  }
}

/**
 * Carga todos los archivos de energía eléctrica y los consolida
 */
export async function loadEnergiaElectricaData(): Promise<EnergiaElectricaRecord[]> {
  const allRecords: EnergiaElectricaRecord[] = [];
  
  for (const path of UPME_DATA_PATHS.energia) {
    const records = await parseCSV<EnergiaElectricaRecord>(path);
    allRecords.push(...records);
  }
  
  return allRecords;
}

/**
 * Carga todos los archivos de potencia máxima y los consolida
 */
export async function loadPotenciaMaximaData(): Promise<PotenciaMaximaRecord[]> {
  const allRecords: PotenciaMaximaRecord[] = [];
  
  for (const path of UPME_DATA_PATHS.potencia) {
    const records = await parseCSV<PotenciaMaximaRecord>(path);
    allRecords.push(...records);
  }
  
  return allRecords;
}

/**
 * Carga todos los archivos de capacidad instalada y los consolida
 */
export async function loadCapacidadInstaladaData(): Promise<CapacidadInstaladaRecord[]> {
  const allRecords: CapacidadInstaladaRecord[] = [];
  
  for (const path of UPME_DATA_PATHS.capacidad) {
    const records = await parseCSV<CapacidadInstaladaRecord>(path);
    allRecords.push(...records);
  }
  
  return allRecords;
}

/**
 * Carga el archivo consolidado de gas natural
 */
export async function loadGasNaturalData(): Promise<GasNaturalRecord[]> {
  const allRecords: GasNaturalRecord[] = [];
  
  for (const path of UPME_DATA_PATHS.gas) {
    const records = await parseCSV<GasNaturalRecord>(path);
    allRecords.push(...records);
  }
  
  return allRecords;
}

