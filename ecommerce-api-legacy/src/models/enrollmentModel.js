const { run, all } = require('../config/database');

async function create(userId, courseId) {
  const { lastID } = await run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
    userId,
    courseId,
  ]);
  return lastID;
}

function findByUserId(userId) {
  return all('SELECT * FROM enrollments WHERE user_id = ?', [userId]);
}

async function removeByUserId(userId) {
  const { changes } = await run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
  return changes;
}

module.exports = { create, findByUserId, removeByUserId };
