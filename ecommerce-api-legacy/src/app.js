const express = require('express');

const settings = require('./config/settings');
const database = require('./config/database');
const routes = require('./routes');
const { errorHandler } = require('./middlewares/errorHandler');

async function createApp() {
  await database.initSchema();
  await database.seed();

  const app = express();
  app.use(express.json());
  app.use(routes);
  app.use(errorHandler);

  return app;
}

if (require.main === module) {
  createApp().then((app) => {
    app.listen(settings.port, () => {
      console.log(`LMS API rodando na porta ${settings.port}...`);
    });
  });
}

module.exports = { createApp };
