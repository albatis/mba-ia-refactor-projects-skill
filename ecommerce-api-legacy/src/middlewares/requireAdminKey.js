const { adminApiKey } = require('../config/settings');
const { AppError } = require('./errorHandler');

function requireAdminKey(req, res, next) {
  const key = req.headers['x-admin-key'];
  if (key !== adminApiKey) {
    return next(new AppError('Chave de administrador inválida ou ausente', 401));
  }
  return next();
}

module.exports = requireAdminKey;
