const courseModel = require('../models/courseModel');

async function financialReport(req, res, next) {
  try {
    const rows = await courseModel.findFinancialReportRows();

    const report = [];
    const byCourseId = new Map();

    for (const row of rows) {
      let entry = byCourseId.get(row.course_id);
      if (!entry) {
        entry = { course: row.course_title, revenue: 0, students: [] };
        byCourseId.set(row.course_id, entry);
        report.push(entry);
      }
      if (row.student_name) {
        if (row.payment_status === 'PAID') entry.revenue += row.paid_amount;
        entry.students.push({ student: row.student_name, paid: row.paid_amount || 0 });
      }
    }

    res.json(report);
  } catch (err) {
    next(err);
  }
}

module.exports = { financialReport };
