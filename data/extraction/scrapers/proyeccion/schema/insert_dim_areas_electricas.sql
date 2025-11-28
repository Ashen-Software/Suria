-- INSERTs para dim_areas_electricas
-- Generado automáticamente a partir de CSVs normalizados
--
-- Uso: Ejecutar estos INSERTs después de crear la tabla
-- Los INSERTs usan ON CONFLICT para evitar duplicados

INSERT INTO public.dim_areas_electricas (codigo, nombre, categoria, descripcion)
VALUES ('AREA_SIN_TOTAL', 'Total Áreas SIN', 'area_sin', NULL)
ON CONFLICT (codigo) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  categoria = EXCLUDED.categoria,
  descripcion = EXCLUDED.descripcion;

INSERT INTO public.dim_areas_electricas (codigo, nombre, categoria, descripcion)
VALUES ('SIN_GCE_ME_GD', 'SIN con GCE, ME y Generación Distribuida', 'combinado', NULL)
ON CONFLICT (codigo) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  categoria = EXCLUDED.categoria,
  descripcion = EXCLUDED.descripcion;

INSERT INTO public.dim_areas_electricas (codigo, nombre, categoria, descripcion)
VALUES ('GD_TOTAL', 'Total Generación Distribuida', 'gd', NULL)
ON CONFLICT (codigo) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  categoria = EXCLUDED.categoria,
  descripcion = EXCLUDED.descripcion;

INSERT INTO public.dim_areas_electricas (codigo, nombre, categoria, descripcion)
VALUES ('SIN', 'Sistema Interconectado Nacional', 'nacional', NULL)
ON CONFLICT (codigo) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  categoria = EXCLUDED.categoria,
  descripcion = EXCLUDED.descripcion;
