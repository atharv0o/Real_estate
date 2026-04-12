FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend /app

ENV HOSTNAME=0.0.0.0
ENV PORT=3000

CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0", "-p", "3000"]
