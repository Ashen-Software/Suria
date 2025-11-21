import type { Route } from "./+types/home";
import { useTodos } from "../hooks/useTodos";
import { TodosList } from "../components/TodosList";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Supabase Todos Test" },
    { name: "description", content: "Testing Supabase connection" },
  ];
}

export default function Home() {
  const { todos, loading, error } = useTodos();

  return <TodosList todos={todos} loading={loading} error={error} />;
}
