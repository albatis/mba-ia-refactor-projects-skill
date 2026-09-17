const { get, all } = require('../config/database');

function findActiveById(id) {
  return get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
}

function findAll() {
  return all('SELECT * FROM courses');
}

// Uma única query com LEFT JOIN em vez de N+1 consultas por curso/matrícula
// (curso -> matrículas -> usuário + pagamento, uma a uma, como no código legado).
function findFinancialReportRows() {
  return all(`
    SELECT c.id AS course_id, c.title AS course_title,
           u.name AS student_name,
           p.amount AS paid_amount, p.status AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.enrollment_id = e.id
    ORDER BY c.id
  `);
}

module.exports = { findActiveById, findAll, findFinancialReportRows };
