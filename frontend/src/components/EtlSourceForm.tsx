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
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label">
          <span className="label-text">Nombre</span>
        </label>
        <input
          type="text"
          className="input input-bordered w-full"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
        />
      </div>

      <div>
        <label className="label">
          <span className="label-text">Tipo</span>
        </label>
        <input
          type="text"
          className="input input-bordered w-full"
          value={formData.type || ''}
          onChange={(e) => setFormData({ ...formData, type: e.target.value || null })}
        />
      </div>

      <div>
        <label className="label">
          <span className="label-text">Schedule Cron</span>
        </label>
        <input
          type="text"
          className="input input-bordered w-full"
          value={formData.schedule_cron}
          onChange={(e) => setFormData({ ...formData, schedule_cron: e.target.value })}
          required
          placeholder="0 0 * * *"
        />
      </div>

      <div className="form-control">
        <label className="label cursor-pointer">
          <span className="label-text">Activo</span>
          <input
            type="checkbox"
            className="checkbox"
            checked={formData.active}
            onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
          />
        </label>
      </div>

      <div>
        <label className="label">
          <span className="label-text">Config (JSON)</span>
        </label>
        <textarea
          className="textarea textarea-bordered w-full"
          rows={4}
          value={configJson}
          onChange={(e) => setConfigJson(e.target.value)}
          placeholder="{}"
        />
      </div>

      <div>
        <label className="label">
          <span className="label-text">Storage Config (JSON)</span>
        </label>
        <textarea
          className="textarea textarea-bordered w-full"
          rows={4}
          value={storageConfigJson}
          onChange={(e) => setStorageConfigJson(e.target.value)}
          placeholder="{}"
        />
      </div>

      {jsonError && (
        <div className="alert alert-error">
          <span>{jsonError}</span>
        </div>
      )}

      <div className="flex gap-2">
        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {isLoading ? 'Guardando...' : 'Guardar'}
        </button>
        <button type="button" className="btn" onClick={onCancel}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
