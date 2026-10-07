const fs = require('fs');
const path = require('path');

const config = {
    http_host: process.env.HTTP_HOST || '0.0.0.0',
    http_port: parseInt(process.env.HTTP_PORT || '15100', 10),
    connection_timeout: parseInt(process.env.CONNECTION_TIMEOUT || '300000', 10),
    backend_auth_token: process.env.EVENT_DAEMON_KEY || 'lqdoj', // EVENT_DAEMON_KEY in local_settings.py
    allowed_origins: process.env.ALLOWED_ORIGINS
        ? process.env.ALLOWED_ORIGINS.split(',').map(s => s.trim())
        : [
            'http://127.0.0.1:8000',
            'http://localhost:8000',
            'http://localhost:8001',
        ],
    max_subscriptions_per_connection: 64,
};

// Keep machine-specific secrets in the ignored config.local.js file.
const localConfigPath = path.join(__dirname, 'config.local.js');
module.exports = fs.existsSync(localConfigPath)
    ? Object.assign(config, require(localConfigPath))
    : config;

