const { run, get } = require('../config/database');

function findByEmail(email) {
  return get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
}

function findById(id) {
  return get('SELECT id, name, email FROM users WHERE id = ?', [id]);
}

async function create(name, email, passwordHash) {
  const { lastID } = await run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
    name,
    email,
    passwordHash,
  ]);
  return lastID;
}

async function remove(id) {
  const { changes } = await run('DELETE FROM users WHERE id = ?', [id]);
  return changes;
}

module.exports = { findByEmail, findById, create, remove };
