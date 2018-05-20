FROM node:8 as builder
WORKDIR /data

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run generate

FROM nginx:alpine

COPY --from=builder /data/dist /usr/share/nginx/html
