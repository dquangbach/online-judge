FROM node:18-alpine

WORKDIR /app

# Copy dependency specifications
COPY websocket/package*.json ./
RUN npm ci --only=production || npm install --production

# Copy application source code
COPY websocket/ ./

# Expose default port
EXPOSE 15100

CMD ["node", "daemon.js"]
