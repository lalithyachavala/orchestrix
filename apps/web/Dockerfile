FROM node:20-slim
WORKDIR /app

# NEXT_PUBLIC_* is baked at BUILD time. Pass the API URL as a build arg so the
# client bundle points at the deployed API (Render passes this from render.yaml).
ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE

COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build
# Bind to $PORT (Render injects it; falls back to 3000 locally).
CMD ["sh", "-c", "node_modules/.bin/next start -p ${PORT:-3000}"]
