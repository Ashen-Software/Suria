import type { EnergiaElectricaRecord, PotenciaMaximaRecord, CapacidadInstaladaRecord, GasNaturalRecord } from '@/types/upme.types';
import { factEnergiaElectricaService } from './factEnergiaElectrica.service';
import { factPotenciaMaximaService } from './factPotenciaMaxima.service';
import { factCapacidadInstaladaService } from './factCapacidadInstalada.service';
import { factDemandaGasNaturalService } from './factDemandaGasNatural.service';

/**
 * Carga todos los registros de energía eléctrica desde Supabase
 */
export async function loadEnergiaElectricaData(): Promise<EnergiaElectricaRecord[]> {
  const { data, error } = await factEnergiaElectricaService.getAll();
  
  if (error) {
    console.error('Error loading energia electrica data:', error);
    throw error;
  }
  
  return data || [];
}

/**
 * Carga todos los registros de potencia máxima desde Supabase
 */
export async function loadPotenciaMaximaData(): Promise<PotenciaMaximaRecord[]> {
  const { data, error } = await factPotenciaMaximaService.getAll();
  
  if (error) {
    console.error('Error loading potencia maxima data:', error);
    throw error;
  }
  
  return data || [];
}

/**
 * Carga todos los registros de capacidad instalada desde Supabase
 */
export async function loadCapacidadInstaladaData(): Promise<CapacidadInstaladaRecord[]> {
  const { data, error } = await factCapacidadInstaladaService.getAll();
  
  if (error) {
    console.error('Error loading capacidad instalada data:', error);
    throw error;
  }
  
  return data || [];
}

/**
 * Carga todos los registros de gas natural desde Supabase
 */
export async function loadGasNaturalData(): Promise<GasNaturalRecord[]> {
  const { data, error } = await factDemandaGasNaturalService.getAll();
  
  if (error) {
    console.error('Error loading gas natural data:', error);
    throw error;
  }
  
  return data || [];
}

