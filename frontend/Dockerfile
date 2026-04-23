FROM node:22-alpine

WORKDIR /app

# Install deps first — this layer caches when only source changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# Vite binds to localhost by default; expose on 0.0.0.0 so Docker can
# forward the port to the host.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
