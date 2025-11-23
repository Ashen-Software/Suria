# Frontend - Proyecto Datos 2025

Aplicación React + TypeScript + Vite con arquitectura escalable y buenas prácticas.

## 🏗️ Arquitectura del Proyecto

```
src/
├── components/          # Componentes reutilizables de UI
│   ├── ProductoList.tsx
│   └── index.ts
├── config/             # Configuración de la aplicación
│   └── supabase.ts     # Cliente de Supabase
├── hooks/              # Custom hooks de React
│   ├── useProductos.ts
│   └── index.ts
├── services/           # Capa de servicios para API
│   ├── producto.service.ts
│   └── index.ts
├── types/              # Definiciones de TypeScript
│   ├── producto.types.ts
│   └── index.ts
├── utils/              # Utilidades y helpers
├── assets/             # Recursos estáticos
├── App.tsx             # Componente principal
├── main.tsx            # Entry point
└── index.css           # Estilos globales
```

## 🎯 Buenas Prácticas Implementadas

### 1. **Separación de Responsabilidades**
- **Components**: Solo presentación y UI
- **Hooks**: Lógica de estado y efectos
- **Services**: Comunicación con APIs
- **Types**: Definiciones de tipos compartidas

### 2. **Path Aliases**
Usa `@/` para importaciones limpias:
```typescript
import { useProductos } from '@/hooks'
import { ProductoList } from '@/components'
import type { Producto } from '@/types'
```

### 3. **TypeScript Estricto**
- Tipos explícitos en toda la aplicación
- Interfaces bien definidas
- Type safety completo

### 4. **Patrón Singleton en Services**
Los servicios usan el patrón Singleton para gestión eficiente de instancias.

### 5. **Manejo de Errores**
- Validación de variables de entorno
- Manejo consistente de errores en servicios
- Feedback visual de estados (loading, error, empty)

### 6. **Custom Hooks Reutilizables**
Encapsulan lógica compleja y pueden reutilizarse en múltiples componentes.

## 🚀 Instalación y Configuración

1. **Instalar dependencias:**
```bash
pnpm install
```

2. **Configurar variables de entorno:**
Crea un archivo `.env` con tus credenciales de Supabase:
```bash
VITE_SUPABASE_URL=tu-url-de-supabase
VITE_SUPABASE_ANON_KEY=tu-anon-key
```

3. **Ejecutar en desarrollo:**
```bash
pnpm dev
```

4. **Build para producción:**
```bash
pnpm build
```

## 📦 Dependencias Principales

- **React 19** - UI Framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Supabase** - Backend as a Service
- **TailwindCSS + DaisyUI** - Estilos
- **AG Grid** - Tablas de datos

## 🔧 Scripts Disponibles

- `pnpm dev` - Inicia servidor de desarrollo
- `pnpm build` - Compila para producción
- `pnpm lint` - Ejecuta ESLint
- `pnpm preview` - Preview del build de producción

## 📁 Estructura de Archivos Creada

### Tipos (`types/`)
Define interfaces y tipos TypeScript reutilizables para mantener consistencia en toda la aplicación.

### Servicios (`services/`)
Capa de abstracción para interactuar con Supabase. Encapsula toda la lógica de API y proporciona métodos reutilizables como:
- `getAll()` - Obtener todos los productos
- `getById(id)` - Obtener un producto específico
- `create(producto)` - Crear nuevo producto
- `update(id, producto)` - Actualizar producto
- `delete(id)` - Eliminar producto

### Hooks (`hooks/`)
Custom hooks que encapsulan lógica de estado y efectos. Ejemplo: `useProductos()` maneja el estado de productos, loading y errores.

### Componentes (`components/`)
Componentes reutilizables y presentacionales. `ProductoList` maneja la visualización de productos con estados de loading, error y empty.

## 📚 Próximos Pasos

- [ ] Implementar React Router para navegación
- [ ] Agregar pruebas unitarias (Vitest)
- [ ] Implementar Context API o Zustand para estado global
- [ ] Agregar más servicios según necesidades
- [ ] Implementar lazy loading de componentes
- [ ] Agregar interceptores para peticiones HTTP
