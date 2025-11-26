const { chromium } = require('playwright');

async function startServer() {
  const browserServer = await chromium.launchServer({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
    ],
    port: 3000,
    host: '0.0.0.0',
  });

  const wsEndpoint = browserServer.wsEndpoint();
  console.log(`Browser server started at: ${wsEndpoint}`);
  console.log('Waiting for connections...');

  process.on('SIGINT', async () => {
    await browserServer.close();
    process.exit(0);
  });
}

startServer().catch(console.error);
