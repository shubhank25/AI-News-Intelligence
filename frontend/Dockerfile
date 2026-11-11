
# Purpose: Build the React frontend and serve its production assets using Nginx.

# Stage 1: Build the React application.
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies.
COPY package*.json ./

RUN npm ci

# Copy frontend source code.
COPY . .

# Build the production frontend.
RUN npm run build


# Stage 2: Serve the production build using Nginx.
FROM nginx:alpine

# Copy the generated frontend assets.
COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose the Nginx web server port.
EXPOSE 80

# Run Nginx in the foreground.
CMD ["nginx", "-g", "daemon off;"]
