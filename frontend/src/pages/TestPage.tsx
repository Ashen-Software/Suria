import { Link } from 'react-router';

export function TestPage() {
  return (
    <div className="p-4">
      <div className="card bg-base-100 shadow-xl">
        <div className="card-body">
          <h2 className="card-title">Página de Prueba</h2>
          <p>Esta es una página de prueba para demostrar la navegación con React Router.</p>
          <div className="card-actions justify-end">
            <Link to="/" className="btn btn-primary">
              Volver a Productos
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
