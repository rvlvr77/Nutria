# Imagen para desarrollo local (docker compose). En producción el frontend se despliega en Vercel.
FROM node:20-alpine

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
