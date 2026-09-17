const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');

const db = new sqlite3.Database(':memory:');

function run(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function callback(err) {
      if (err) return reject(err);
      resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
}

function get(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
  });
}

function all(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
  });
}

async function withTransaction(fn) {
  await run('BEGIN TRANSACTION');
  try {
    const result = await fn();
    await run('COMMIT');
    return result;
  } catch (err) {
    await run('ROLLBACK');
    throw err;
  }
}

const SCHEMA = `
  CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
  CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
  CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
  CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
  CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

function initSchema() {
  return new Promise((resolve, reject) => {
    db.exec(SCHEMA, (err) => (err ? reject(err) : resolve()));
  });
}

async function seed() {
  const passwordHash = await bcrypt.hash('123', 10);
  await run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
    'Leonan',
    'leonan@fullcycle.com.br',
    passwordHash,
  ]);
  await run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', ['Clean Architecture', 997.0]);
  await run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', ['Docker', 497.0]);
  const enrollment = await run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
  await run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
    enrollment.lastID,
    997.0,
    'PAID',
  ]);
}

module.exports = { db, run, get, all, withTransaction, initSchema, seed };
