FROM oven/bun:latest AS base
WORKDIR /usr/src
COPY ["./web/package.json", "./web/bun.lock", "./"]
RUN bun install
COPY ./web ./
ARG BUILD
ENV VITE_BUILD_VERSION=$BUILD 

FROM base AS build
RUN bun run build

FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
COPY ./api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY ./api /app
COPY --from=build /usr/src/dist /app/www
RUN chmod -R +rx /app/www

