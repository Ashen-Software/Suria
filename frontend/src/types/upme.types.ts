// Tipos para datos de UPME - Proyección de Demanda

export interface EnergiaElectricaRecord {
  period_key: string; // YYYY-MM-DD
  periodicidad: 'mensual' | 'anual';
  metric: 'energia';
  unidad: string;
  ambito: string;
  descriptor: string;
  escenario: 'ESC_BAJO' | 'ESC_MEDIO' | 'ESC_ALTO';
  valor: number;
  revision: string;
  year_span: string;
  sheet_name: string;
  source_file: string;
}

export interface PotenciaMaximaRecord {
  period_key: string;
  periodicidad: 'mensual' | 'anual';
  metric: 'potencia';
  unidad: string;
  ambito: string;
  descriptor: string;
  escenario: 'ESC_BAJO' | 'ESC_MEDIO' | 'ESC_ALTO';
  valor: number;
  revision: string;
  year_span: string;
  sheet_name: string;
  source_file: string;
}

export interface CapacidadInstaladaRecord {
  period_key: string;
  periodicidad: 'mensual' | 'anual';
  metric: 'capacidad';
  unidad: string;
  ambito: string;
  descriptor: string;
  escenario: 'ESC_BAJO' | 'ESC_MEDIO' | 'ESC_ALTO';
  valor: number;
  revision: string;
  year_span: string;
  sheet_name: string;
  source_file: string;
}

export interface GasNaturalRecord {
  period_key: string;
  periodicidad: 'mensual' | 'anual';
  categoria: 'COMPRESORES' | 'INDUSTRIAL' | 'PETROLERO' | 'PETROQUIMICO' | 'RESIDENCIAL' | 'TERCIARIO' | 'TERMOELECTRICO' | 'GNC_TRANSPORTE' | 'GNL_TRANSPORTE' | 'AGREGADO';
  region: string | null;
  nodo: string | null;
  escenario: 'ESC_BAJO' | 'ESC_MEDIO' | 'ESC_ALTO';
  valor: number;
  unidad: string;
  revision: string;
  year_span: string;
  sheet_name: string;
  source_file: string;
}

export type UPMERecord = EnergiaElectricaRecord | PotenciaMaximaRecord | CapacidadInstaladaRecord | GasNaturalRecord;

