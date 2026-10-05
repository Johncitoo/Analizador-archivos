# --- Desarrollo: servidor de Vite con recarga automática (lo usa docker-compose) ---
FROM node:22-alpine AS dev
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]

# --- Build: compila React a archivos estáticos (HTML, JS, CSS) ---
FROM dev AS build
# URL pública de la API; Vite la incrusta en el JS al compilar
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# --- Producción: nginx sirve los archivos compilados ---
FROM nginx:1.29-alpine AS prod
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
# Railway define $PORT; nginx lo reemplaza en la plantilla al arrancar
ENV PORT=8080
EXPOSE 8080
