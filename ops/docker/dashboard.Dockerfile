FROM node:22-bookworm-slim

WORKDIR /app

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

COPY apps/dashboard-web/package.json /app/package.json
COPY apps/dashboard-web/package-lock.json /app/package-lock.json

RUN npm ci

COPY apps/dashboard-web /app

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
