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
import { useDimTiempo } from '@/hooks/useDimTiempo'
import type { DimTiempo } from '@/types/dim_tiempo.types'

const columnHelper = createColumnHelper<DimTiempo>()

export function DimTiempoViewer() {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 20 })

  const { data, isLoading, error } = useDimTiempo({ 
    page: pagination.pageIndex, 
    pageSize: pagination.pageSize 
  })
  const dimTiempoData = data?.data || []
  const totalCount = data?.count || 0

  const columns = useMemo(
    () => [
      columnHelper.accessor('id', {
        header: 'ID',
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor('fecha', {
        header: 'Fecha',
        cell: (info) => new Date(info.getValue()).toLocaleDateString('es-ES'),
      }),
      columnHelper.accessor('anio', {
        header: 'Año',
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor('mes', {
        header: 'Mes',
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor('nombre_mes', {
        header: 'Nombre Mes',
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor('trimestre', {
        header: 'Trimestre',
        cell: (info) => info.getValue() ? `Q${info.getValue()}` : 'N/A',
      }),
      columnHelper.accessor('semestre', {
        header: 'Semestre',
        cell: (info) => info.getValue() ? `S${info.getValue()}` : 'N/A',
      }),
      columnHelper.accessor('es_proyeccion', {
        header: 'Proyección',
        cell: (info) => (
          <span className={`badge ${info.getValue() ? 'badge-warning' : 'badge-success'}`}>
            {info.getValue() ? 'Sí' : 'No'}
          </span>
        ),
      }),
    ],
    []
  )

  const pageCount = Math.ceil(totalCount / pagination.pageSize)

  const table = useReactTable({
    data: dimTiempoData,
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
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Dimensión Tiempo</h1>
        <p className="text-sm text-gray-500 mt-1">Vista de solo lectura</p>
      </div>

      {dimTiempoData && dimTiempoData.length === 0 ? (
        <div className="alert alert-info">
          <span>No hay datos disponibles en la dimensión tiempo</span>
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
              {[20, 30, 40, 50, 100].map((pageSize) => (
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
    </div>
  )
}
