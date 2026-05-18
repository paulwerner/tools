FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci || npm install

FROM node:20-alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS prod
RUN npm install -g sirv-cli
WORKDIR /app
COPY --from=build /app/build ./build
EXPOSE 3000
CMD ["sirv", "build", "--host", "0.0.0.0", "--port", "3000", "--single"]
