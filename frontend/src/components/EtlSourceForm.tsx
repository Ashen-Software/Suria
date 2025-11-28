import { useState, useEffect } from 'react'
import type { EtlSource, EtlSourceFormData } from '@/types/etlSource.types'

interface EtlSourceFormProps {
  etlSource?: EtlSource
  onSubmit: (data: EtlSourceFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

export function EtlSourceForm({ etlSource, onSubmit, onCancel, isLoading }: EtlSourceFormProps) {
  const [formData, setFormData] = useState<EtlSourceFormData>({
    name: '',
    active: false,
    type: null,
    schedule_cron: '',
    config: {},
    storage_config: {},
  })

  const [configJson, setConfigJson] = useState('')
  const [storageConfigJson, setStorageConfigJson] = useState('')
  const [jsonError, setJsonError] = useState<string | null>(null)

  useEffect(() => {
    if (etlSource) {
      setFormData({
        name: etlSource.name,
        active: etlSource.active,
        type: etlSource.type,
        schedule_cron: etlSource.schedule_cron,
        config: etlSource.config,
        storage_config: etlSource.storage_config,
      })
      setConfigJson(JSON.stringify(etlSource.config, null, 2))
      setStorageConfigJson(JSON.stringify(etlSource.storage_config, null, 2))
    }
  }, [etlSource])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setJsonError(null)

    try {
      const config = configJson.trim() ? JSON.parse(configJson) : {}
      const storage_config = storageConfigJson.trim() ? JSON.parse(storageConfigJson) : {}

      onSubmit({
        ...formData,
        config,
        storage_config,
      })
    } catch (error) {
      setJsonError('JSON inválido en config o storage_config')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium text-base-content/70">Nombre</label>
          <input
            type="text"
            className="input input-bordered w-full rounded-2xl bg-base-100/70"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-base-content/70">Tipo</label>
          <input
            type="text"
            className="input input-bordered w-full rounded-2xl bg-base-100/70"
            value={formData.type || ''}
            onChange={(e) => setFormData({ ...formData, type: e.target.value || null })}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-base-content/70">Schedule Cron</label>
          <input
            type="text"
            className="input input-bordered w-full rounded-2xl bg-base-100/70"
            value={formData.schedule_cron}
            onChange={(e) => setFormData({ ...formData, schedule_cron: e.target.value })}
            required
            placeholder="0 0 * * *"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-base-content/70">Estado</label>
          <div className="glass-panel flex items-center justify-between rounded-2xl p-3">
            <span className="text-sm text-base-content/60">Activo</span>
            <input
              type="checkbox"
              className="toggle toggle-primary"
              checked={formData.active}
              onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
            />
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium text-base-content/70">Config (JSON)</label>
          <textarea
            className="textarea textarea-bordered w-full rounded-2xl bg-base-100/70 font-mono text-sm"
            rows={6}
            value={configJson}
            onChange={(e) => setConfigJson(e.target.value)}
            placeholder="{}"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-base-content/70">Storage Config (JSON)</label>
          <textarea
            className="textarea textarea-bordered w-full rounded-2xl bg-base-100/70 font-mono text-sm"
            rows={6}
            value={storageConfigJson}
            onChange={(e) => setStorageConfigJson(e.target.value)}
            placeholder="{}"
          />
        </div>
      </div>

      {jsonError && (
        <div className="alert alert-error rounded-2xl">
          <span>{jsonError}</span>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button type="submit" className="btn btn-primary rounded-2xl px-6" disabled={isLoading}>
          {isLoading ? 'Guardando...' : 'Guardar'}
        </button>
        <button type="button" className="btn btn-ghost rounded-2xl px-6" onClick={onCancel}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
