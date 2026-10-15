FROM node:20-slim AS build
WORKDIR /srv
COPY package.json package-lock.json ./
RUN npm install --no-audit --no-fund
COPY vite.config.ts tsconfig.json tsconfig.node.json eslint.config.js ./
COPY src ./src
RUN npm run build

FROM nginx:alpine
COPY --from=build /srv/src/dist /usr/share/nginx/html
EXPOSE 80
