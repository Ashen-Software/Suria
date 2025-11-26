export interface EtlSource {
  id: string
  name: string
  active: boolean
  type: string | null
  schedule_cron: string
  config: Record<string, any>
  storage_config: Record<string, any>
  created_at?: string
  updated_at?: string
}

export interface EtlSourceFormData extends Omit<EtlSource, 'id' | 'created_at' | 'updated_at'> {}
