import { useState } from 'react'
import { useEtlSources } from '@/hooks/useEtlSources'
import { useCreateEtlSource, useUpdateEtlSource, useDeleteEtlSource } from '@/hooks/useEtlSourcesMutation'
import { EtlSourceForm } from './EtlSourceForm'
import type { EtlSource, EtlSourceFormData } from '@/types/etlSource.types'

export function EtlSourceList() {
  const { data: etlSources, isLoading, error } = useEtlSources()
  const createMutation = useCreateEtlSource()
  const updateMutation = useUpdateEtlSource()
  const deleteMutation = useDeleteEtlSource()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSource, setEditingSource] = useState<EtlSource | undefined>()

  const handleCreate = () => {
    setEditingSource(undefined)
    setIsModalOpen(true)
  }

  const handleEdit = (source: EtlSource) => {
    setEditingSource(source)
    setIsModalOpen(true)
  }

  const handleDelete = async (id: string) => {
    if (confirm('¿Estás seguro de eliminar esta fuente ETL?')) {
      const result = await deleteMutation.mutateAsync(id)
      if (result.error) {
        alert('Error al eliminar: ' + result.error.message)
      }
    }
  }

  const handleSubmit = async (data: EtlSourceFormData) => {
    if (editingSource) {
      const result = await updateMutation.mutateAsync({ id: editingSource.id, data })
      if (result.error) {
        alert('Error al actualizar: ' + result.error.message)
      } else {
        setIsModalOpen(false)
      }
    } else {
      const result = await createMutation.mutateAsync(data)
      if (result.error) {
        alert('Error al crear: ' + result.error.message)
      } else {
        setIsModalOpen(false)
      }
    }
  }

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="flex items-center justify-center">
          <span className="loading loading-spinner loading-lg"></span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="alert alert-error">
          <span>Error: {error.message}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4">
      <div className="mb-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Fuentes ETL</h1>
        <button className="btn btn-primary" onClick={handleCreate}>
          Crear Nueva
        </button>
      </div>

      {etlSources && etlSources.length === 0 ? (
        <div className="alert alert-info">
          <span>No hay fuentes ETL disponibles</span>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Tipo</th>
                <th>Activo</th>
                <th>Cron</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {etlSources?.map((source) => (
                <tr key={source.id}>
                  <td>{source.name}</td>
                  <td>{source.type || 'N/A'}</td>
                  <td>
                    <span className={`badge ${source.active ? 'badge-success' : 'badge-error'}`}>
                      {source.active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td>{source.schedule_cron}</td>
                  <td>
                    <div className="flex gap-2">
                      <button className="btn btn-sm btn-info" onClick={() => handleEdit(source)}>
                        Editar
                      </button>
                      <button
                        className="btn btn-sm btn-error"
                        onClick={() => handleDelete(source.id)}
                        disabled={deleteMutation.isPending}
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isModalOpen && (
        <dialog className="modal modal-open">
          <div className="modal-box max-w-2xl">
            <h3 className="font-bold text-lg mb-4">
              {editingSource ? 'Editar Fuente ETL' : 'Crear Fuente ETL'}
            </h3>
            <EtlSourceForm
              etlSource={editingSource}
              onSubmit={handleSubmit}
              onCancel={() => setIsModalOpen(false)}
              isLoading={createMutation.isPending || updateMutation.isPending}
            />
          </div>
          <form method="dialog" className="modal-backdrop">
            <button onClick={() => setIsModalOpen(false)}>close</button>
          </form>
        </dialog>
      )}
    </div>
  )
}
