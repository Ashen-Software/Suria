import type { Route } from "./+types/hola";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Hola" },
    { name: "description", content: "Testing Supabase connection" },
  ];
}

export default function Hola() {

  return <div>Hola</div>
}
