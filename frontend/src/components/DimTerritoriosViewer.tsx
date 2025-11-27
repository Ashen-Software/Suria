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
import { useDimTerritorios } from '@/hooks/useDimTerritorios'
import type { DimTerritorios } from '@/types/dim_territorios.types'

const columnHelper = createColumnHelper<DimTerritorios>()

export function DimTerritoriosViewer() {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 20 })

  const { data, isLoading, error } = useDimTerritorios({ 
    page: pagination.pageIndex, 
    pageSize: pagination.pageSize 
  })
  const dimTerritoriosData = data?.data || []
  const totalCount = data?.count || 0

  const columns = useMemo(
    () => [
      columnHelper.accessor('id', {
        header: 'ID',
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor('departamento', {
        header: 'Departamento',
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor('municipio', {
        header: 'Municipio',
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor('divipola', {
        header: 'DIVIPOLA',
        cell: (info) => info.getValue() || 'N/A',
      }),
      columnHelper.accessor('latitud', {
        header: 'Latitud',
        cell: (info) => info.getValue()?.toFixed(7) || 'N/A',
      }),
      columnHelper.accessor('longitud', {
        header: 'Longitud',
        cell: (info) => info.getValue()?.toFixed(7) || 'N/A',
      }),
    ],
    []
  )

  const pageCount = Math.ceil(totalCount / pagination.pageSize)

  const table = useReactTable({
    data: dimTerritoriosData,
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
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Catálogo maestro</p>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-gradient text-3xl font-semibold">Dimensión Territorios</h1>
            <p className="text-sm text-base-content/60">Consulta de solo lectura con paginación inteligente.</p>
          </div>
          <span className="badge badge-outline badge-lg px-4 py-3">
            {totalCount} registros
          </span>
        </div>
      </div>

      {dimTerritoriosData && dimTerritoriosData.length === 0 ? (
        <div className="glass-panel flex flex-col items-center gap-2 py-10 text-center">
          <span className="text-2xl">☁️</span>
          <p className="text-base font-semibold">No hay datos disponibles en la dimensión territorios</p>
          <p className="text-sm text-base-content/60">Carga una nueva fuente para visualizar información.</p>
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
              {[20, 30, 40, 50, 100].map((pageSize) => (
                <option key={pageSize} value={pageSize}>
                  Mostrar {pageSize}
                </option>
              ))}
            </select>
          </div>
        </>
      )}
    </div>
  )
}
