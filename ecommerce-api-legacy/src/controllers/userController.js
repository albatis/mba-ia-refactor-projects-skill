const auditLogModel = require('../models/auditLogModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const userModel = require('../models/userModel');
const { withTransaction } = require('../config/database');
const { AppError } = require('../middlewares/errorHandler');

async function remove(req, res, next) {
  try {
    const userId = req.params.id;

    await withTransaction(async () => {
      const enrollments = await enrollmentModel.findByUserId(userId);
      const enrollmentIds = enrollments.map((enrollment) => enrollment.id);

      await paymentModel.removeByEnrollmentIds(enrollmentIds);
      await enrollmentModel.removeByUserId(userId);

      const changes = await userModel.remove(userId);
      if (changes === 0) throw new AppError('Usuário não encontrado', 404);

      await auditLogModel.record(`Usuário ${userId} removido (cascade de matrículas/pagamentos)`);
    });

    res.json({
      mensagem: 'Usuário removido com sucesso, incluindo matrículas e pagamentos associados',
    });
  } catch (err) {
    next(err);
  }
}

module.exports = { remove };
