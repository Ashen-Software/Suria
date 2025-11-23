# Stage 1: Build
FROM node:24-alpine AS builder

WORKDIR /app

# Declarar build arguments
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

# Establecer como variables de entorno para el build
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

# Copiar archivos de dependencias
COPY package.json pnpm-lock.yaml ./

# Instalar pnpm y dependencias
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Copiar el código fuente
COPY . .

# Build de la aplicación
RUN pnpm run build

# Stage 2: Serve
FROM node:24-alpine

WORKDIR /app

# Instalar un servidor HTTP simple
RUN npm install -g serve

# Copiar los archivos built desde el stage anterior
COPY --from=builder /app/dist ./dist

# Exponer el puerto
EXPOSE 3000

# Comando para iniciar la aplicación
CMD ["serve", "-s", "dist", "-l", "3000"]
