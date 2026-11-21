# Frontend · Expedientes Tiendas 3B (Reto 1)

Aplicación frontend aislada en `frontend/` construida con Next.js (App Router + TypeScript), diseñada para conectarse de forma desacoplada a un backend multiagente (Python + LangChain).

## Variables de entorno

Copia `.env.example` a `.env.local`:

```bash
cp .env.example .env.local
```

- `NEXT_PUBLIC_API_BASE_URL`: URL base del backend HTTP (por ejemplo `http://localhost:8000`).
- `NEXT_PUBLIC_USE_MOCKS`: `true` usa fixtures locales en memoria para desarrollar sin bloquear al backend; `false` consume los endpoints reales bajo `/api/v1/*`.
- `NEXT_PUBLIC_APP_NAME`: título visible en la interfaz.

## Comandos

```bash
npm install
npm run dev        # Servidor local en http://localhost:3000
npm run lint       # ESLint (Next.js + TypeScript)
npm run typecheck  # Verificación de tipos con tsc --noEmit
npm run build      # Compilación de producción
```

## Estructura principal

- `src/lib/contracts/`: esquemas Zod y tipos del contrato JSON con el backend.
- `src/lib/config/`: lectura y validación de variables públicas.
- `src/lib/api/`: cliente HTTP ligero (`fetch` + validación Zod) y adaptador de endpoints.
- `src/lib/mocks/`: datos sintéticos de ejemplo para desarrollo en paralelo.
- `src/hooks/`: hooks de `@tanstack/react-query` (incluye polling para análisis en curso).
- `src/components/ui/`: primitivas base compatibles con shadcn/ui (`Badge`, `Button`, `Card`).
- `src/components/workspace/`: vista inicial conectada al contrato de expedientes.
