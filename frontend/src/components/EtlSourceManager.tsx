import { useState, useMemo } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table'
import { useEtlSources } from '@/hooks/useEtlSources'
import { useCreateEtlSource, useUpdateEtlSource, useDeleteEtlSource } from '@/hooks/useEtlSourcesMutation'
import { EtlSourceForm } from './EtlSourceForm'
import type { EtlSource, EtlSourceFormData } from '@/types/etlSource.types'

const columnHelper = createColumnHelper<EtlSource>()

export function EtlSourceManager() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSource, setEditingSource] = useState<EtlSource | undefined>()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 })

  const { data, isLoading, error } = useEtlSources({ 
    page: pagination.pageIndex, 
    pageSize: pagination.pageSize 
  })
  const etlSources = data?.data || []
  const totalCount = data?.count || 0

  const createMutation = useCreateEtlSource()
  const updateMutation = useUpdateEtlSource()
  const deleteMutation = useDeleteEtlSource()

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

  const columns = useMemo(
    () => [
      columnHelper.accessor('name', {
        header: 'Nombre',
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor('type', {
        header: 'Tipo',
        cell: (info) => info.getValue() || 'N/A',
      }),
      columnHelper.accessor('active', {
        header: 'Activo',
        cell: (info) => (
          <span className={`badge ${info.getValue() ? 'badge-success' : 'badge-error'}`}>
            {info.getValue() ? 'Activo' : 'Inactivo'}
          </span>
        ),
      }),
      columnHelper.accessor('schedule_cron', {
        header: 'Cron',
        cell: (info) => info.getValue(),
      }),
      columnHelper.display({
        id: 'actions',
        header: 'Acciones',
        cell: (props) => (
          <div className="flex gap-2">
            <button className="btn btn-sm btn-info" onClick={() => handleEdit(props.row.original)}>
              Editar
            </button>
            <button
              className="btn btn-sm btn-error"
              onClick={() => handleDelete(props.row.original.id)}
              disabled={deleteMutation.isPending}
            >
              Eliminar
            </button>
          </div>
        ),
      }),
    ],
    [deleteMutation.isPending]
  )

  const pageCount = Math.ceil(totalCount / pagination.pageSize)

  const table = useReactTable({
    data: etlSources,
    columns,
    pageCount,
    state: {
      sorting,
      columnFilters,
      pagination,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    manualPagination: true,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <span className="loading loading-ring loading-lg text-primary"></span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="alert alert-error shadow-lg">
        <span>Error: {error.message}</span>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Orquestación</p>
          <h1 className="text-gradient text-3xl font-semibold">Fuentes ETL</h1>
          <p className="text-sm text-base-content/60">Administra los orígenes de datos y sus configuraciones.</p>
        </div>
        <button className="btn btn-primary rounded-2xl px-6" onClick={handleCreate}>
          Crear nueva fuente
        </button>
      </div>

      {etlSources && etlSources.length === 0 ? (
        <div className="glass-panel flex flex-col items-center gap-2 py-10 text-center">
          <span className="text-2xl">🧭</span>
          <p className="text-base font-semibold">No hay fuentes ETL disponibles</p>
          <p className="text-sm text-base-content/60">Registra la primera para comenzar a orquestar datos.</p>
        </div>
      ) : (
        <>
          <div className="overflow-hidden rounded-3xl border border-base-200/70">
            <div className="overflow-x-auto">
              <table className="table table-pin-rows">
                <thead>
                  {table.getHeaderGroups().map((headerGroup) => (
                    <tr key={headerGroup.id}>
                      {headerGroup.headers.map((header) => (
                        <th key={header.id} className="bg-base-200/60 text-xs uppercase tracking-wide text-base-content/60">
                          {header.isPlaceholder ? null : (
                            <button
                              type="button"
                              className={`flex items-center gap-1 ${header.column.getCanSort() ? 'cursor-pointer select-none' : ''}`}
                              onClick={header.column.getToggleSortingHandler()}
                            >
                              {flexRender(header.column.columnDef.header, header.getContext())}
                              {{
                                asc: '↑',
                                desc: '↓',
                              }[header.column.getIsSorted() as string] ?? ''}
                            </button>
                          )}
                        </th>
                      ))}
                    </tr>
                  ))}
                </thead>
                <tbody>
                  {table.getRowModel().rows.map((row) => (
                    <tr key={row.id} className="hover:bg-base-200/30">
                      {row.getVisibleCells().map((cell) => (
                        <td key={cell.id} className="text-sm">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-base-200/70 bg-base-200/40 p-3 text-sm">
            <button className="btn btn-sm btn-ghost" onClick={() => table.setPageIndex(0)} disabled={!table.getCanPreviousPage()}>
              {'«'}
            </button>
            <button className="btn btn-sm btn-ghost" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
              {'‹'}
            </button>
            <button className="btn btn-sm btn-ghost" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
              {'›'}
            </button>
            <button className="btn btn-sm btn-ghost" onClick={() => table.setPageIndex(table.getPageCount() - 1)} disabled={!table.getCanNextPage()}>
              {'»'}
            </button>
            <span className="font-medium">
              Página {table.getState().pagination.pageIndex + 1} de {table.getPageCount()}
            </span>
            <select
              className="select select-sm select-bordered"
              value={table.getState().pagination.pageSize}
              onChange={(e) => {
                table.setPageSize(Number(e.target.value))
              }}
            >
              {[10, 20, 30, 40, 50].map((pageSize) => (
                <option key={pageSize} value={pageSize}>
                  Mostrar {pageSize}
                </option>
              ))}
            </select>
            <span className="text-base-content/60">Total: {totalCount}</span>
          </div>
        </>
      )}

      {isModalOpen && (
        <dialog className="modal modal-open">
          <div className="modal-box max-w-3xl rounded-3xl bg-base-100/95">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-base-content/50">Configuración</p>
                <h3 className="text-2xl font-semibold">
                  {editingSource ? 'Editar fuente ETL' : 'Crear fuente ETL'}
                </h3>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => setIsModalOpen(false)}>
                Cerrar
              </button>
            </div>
            <EtlSourceForm
              etlSource={editingSource}
              onSubmit={handleSubmit}
              onCancel={() => setIsModalOpen(false)}
              isLoading={createMutation.isPending || updateMutation.isPending}
            />
          </div>
          <form method="dialog" className="modal-backdrop">
            <button aria-label="Cerrar" onClick={() => setIsModalOpen(false)}>
              cerrar
            </button>
          </form>
        </dialog>
      )}
    </div>
  )
}
