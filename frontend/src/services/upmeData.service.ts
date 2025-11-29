import type { EnergiaElectricaRecord, PotenciaMaximaRecord, CapacidadInstaladaRecord, GasNaturalRecord } from '@/types/upme.types';
import { factEnergiaElectricaService } from './factEnergiaElectrica.service';
import { factPotenciaMaximaService } from './factPotenciaMaxima.service';
import { factCapacidadInstaladaService } from './factCapacidadInstalada.service';
import { factDemandaGasNaturalService } from './factDemandaGasNatural.service';

/**
 * Carga todos los registros de energía eléctrica desde Supabase (modo completo).
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
 * Carga una página de registros de energía eléctrica (para carga incremental).
 */
export async function loadEnergiaElectricaPage(page: number, pageSize: number): Promise<EnergiaElectricaRecord[]> {
  const from = page * pageSize;
  const to = from + pageSize - 1;

  const { data, error } = await factEnergiaElectricaService.getPage(from, to);

  if (error) {
    console.error('Error loading energia electrica page:', error);
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
 * Carga una página de registros de potencia máxima (para carga incremental).
 */
export async function loadPotenciaMaximaPage(page: number, pageSize: number): Promise<PotenciaMaximaRecord[]> {
  const from = page * pageSize;
  const to = from + pageSize - 1;

  const { data, error } = await factPotenciaMaximaService.getPage(from, to);

  if (error) {
    console.error('Error loading potencia maxima page:', error);
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
 * Carga una página de registros de capacidad instalada (para carga incremental).
 */
export async function loadCapacidadInstaladaPage(page: number, pageSize: number): Promise<CapacidadInstaladaRecord[]> {
  const from = page * pageSize;
  const to = from + pageSize - 1;

  const { data, error } = await factCapacidadInstaladaService.getPage(from, to);

  if (error) {
    console.error('Error loading capacidad instalada page:', error);
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

/**
 * Carga una página de registros de gas natural (para carga incremental).
 */
export async function loadGasNaturalPage(page: number, pageSize: number): Promise<GasNaturalRecord[]> {
  const from = page * pageSize;
  const to = from + pageSize - 1;

  const { data, error } = await factDemandaGasNaturalService.getPage(from, to);

  if (error) {
    console.error('Error loading gas natural page:', error);
    throw error;
  }

  return data || [];
}

