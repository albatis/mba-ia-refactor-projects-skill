try {
  require('dotenv').config();
} catch (err) {
  // dotenv é opcional em produção, onde as variáveis já vêm do ambiente
}

const settings = {
  port: parseInt(process.env.PORT || '3000', 10),
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'test-gateway-key-change-me',
  adminApiKey: process.env.ADMIN_API_KEY || 'dev-admin-key-change-me',
};

module.exports = settings;
