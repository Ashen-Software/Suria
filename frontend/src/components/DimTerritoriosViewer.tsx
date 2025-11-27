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
        <h1 className="text-2xl font-bold">Dimensión Territorios</h1>
        <p className="text-sm text-gray-500 mt-1">Vista de solo lectura</p>
      </div>

      {dimTerritoriosData && dimTerritoriosData.length === 0 ? (
        <div className="alert alert-info">
          <span>No hay datos disponibles en la dimensión territorios</span>
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
