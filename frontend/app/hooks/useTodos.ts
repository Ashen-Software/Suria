import { useState, useEffect } from "react";
import supabase from "../utils/supabase";

export interface Todo {
  id: string;
  [key: string]: any;
}

export function useTodos() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function getTodos() {
      try {
        const { data, error } = await supabase.from("productos").select();

        if (error) {
          setError(error.message);
        } else if (data) {
          setTodos(data);
        }
      } catch (err) {
        setError("Error al conectar con Supabase");
      } finally {
        setLoading(false);
      }
    }

    getTodos();
  }, []);

  return { todos, loading, error };
}
