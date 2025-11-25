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

export function EtlSourceList() {
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
        <>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th key={header.id}>
                        {header.isPlaceholder ? null : (
                          <div
                            className={header.column.getCanSort() ? 'cursor-pointer select-none' : ''}
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            {flexRender(header.column.columnDef.header, header.getContext())}
                            {{
                              asc: ' 🔼',
                              desc: ' 🔽',
                            }[header.column.getIsSorted() as string] ?? null}
                          </div>
                        )}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center gap-2 mt-4">
            <button
              className="btn btn-sm"
              onClick={() => table.setPageIndex(0)}
              disabled={!table.getCanPreviousPage()}
            >
              {'<<'}
            </button>
            <button
              className="btn btn-sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              {'<'}
            </button>
            <button className="btn btn-sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
              {'>'}
            </button>
            <button
              className="btn btn-sm"
              onClick={() => table.setPageIndex(table.getPageCount() - 1)}
              disabled={!table.getCanNextPage()}
            >
              {'>>'}
            </button>
            <span className="flex items-center gap-1">
              <div>Página</div>
              <strong>
                {table.getState().pagination.pageIndex + 1} de {table.getPageCount()}
              </strong>
            </span>
            <select
              className="select select-bordered select-sm"
              value={table.getState().pagination.pageSize}
              onChange={(e) => {
                table.setPageSize(Number(e.target.value))
              }}
            >
              {[1, 20, 30, 40, 50].map((pageSize) => (
                <option key={pageSize} value={pageSize}>
                  Mostrar {pageSize}
                </option>
              ))}
            </select>
            <span className="text-sm">
              Total: {totalCount} registros
            </span>
          </div>
        </>
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
