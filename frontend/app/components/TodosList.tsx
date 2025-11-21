import type { Todo } from "../hooks/useTodos";

interface TodosListProps {
  todos: Todo[];
  loading: boolean;
  error: string | null;
}

export function TodosList({ todos, loading, error }: TodosListProps) {
  if (loading) {
    return <div style={{ padding: "2rem" }}>Cargando...</div>;
  }

  if (error) {
    return <div style={{ padding: "2rem", color: "red" }}>Error: {error}</div>;
  }

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Todos desde Supabase</h1>
      {todos.length === 0 ? (
        <p>No hay todos disponibles</p>
      ) : (
        <ul>
          {todos.map((todo) => (
            <li key={todo.id}>{JSON.stringify(todo)}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
