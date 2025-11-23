import type { Producto } from "@/types/producto.types";

interface ProductoListProps {
  productos: Producto[];
  loading?: boolean;
  error?: Error | null;
}

export function ProductoList({ productos, loading, error }: ProductoListProps) {
  if (loading) {
    return (
      <div className="p-4">
        <div className="flex items-center justify-center">
          <span className="loading loading-spinner loading-lg"></span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="alert alert-error">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="stroke-current shrink-0 h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>Error: {error.message}</span>
        </div>
      </div>
    );
  }

  if (productos.length === 0) {
    return (
      <div className="p-4">
        <div className="alert alert-info">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            className="stroke-current shrink-0 w-6 h-6"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            ></path>
          </svg>
          <span>No hay productos disponibles</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <ul className="list bg-base-100 rounded-box shadow-md">
        {productos.map((producto) => (
          <li key={producto.id} className="list-row">
            <div className="flex flex-col">
              <span className="font-semibold">{producto.nombre}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
