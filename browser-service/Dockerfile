FROM mcr.microsoft.com/playwright:v1.56.0-jammy

WORKDIR /app

# Copy server script
COPY server.js .

# Install playwright (matching client version)
RUN npm init -y && npm install playwright@1.56.0

# Expose ports (3000 for HTTP, 3001 for WebSocket)
EXPOSE 3000
EXPOSE 3001

# Run our custom server that uses launchServer
CMD ["node", "server.js"]
