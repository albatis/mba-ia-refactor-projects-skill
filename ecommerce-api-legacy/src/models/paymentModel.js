const { run } = require('../config/database');

async function create(enrollmentId, amount, status) {
  const { lastID } = await run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
    enrollmentId,
    amount,
    status,
  ]);
  return lastID;
}

async function removeByEnrollmentIds(enrollmentIds) {
  if (enrollmentIds.length === 0) return 0;
  const placeholders = enrollmentIds.map(() => '?').join(',');
  const { changes } = await run(`DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
  return changes;
}

module.exports = { create, removeByEnrollmentIds };
