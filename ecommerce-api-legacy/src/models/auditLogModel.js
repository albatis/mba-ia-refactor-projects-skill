const { run } = require('../config/database');

function record(action) {
  return run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
}

module.exports = { record };
