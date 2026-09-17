const bcrypt = require('bcryptjs');

const auditLogModel = require('../models/auditLogModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const userModel = require('../models/userModel');
const paymentGateway = require('../services/paymentGatewayService');
const { withTransaction } = require('../config/database');
const { AppError } = require('../middlewares/errorHandler');

async function checkout(req, res, next) {
  try {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

    if (!name || !email || !courseId || !cardNumber) {
      throw new AppError('Dados obrigatórios ausentes (usr, eml, c_id, card)', 400);
    }

    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new AppError('Curso não encontrado', 404);

    let user = await userModel.findByEmail(email);
    if (!user) {
      const passwordHash = await bcrypt.hash(password || '123456', 10);
      const userId = await userModel.create(name, email, passwordHash);
      user = { id: userId };
    }

    const authorization = paymentGateway.authorize(cardNumber);
    if (authorization.status === 'DENIED') {
      throw new AppError('Pagamento recusado', 400);
    }

    const enrollmentId = await withTransaction(async () => {
      const id = await enrollmentModel.create(user.id, courseId);
      await paymentModel.create(id, course.price, authorization.status);
      await auditLogModel.record(`Checkout curso ${courseId} por usuário ${user.id}`);
      return id;
    });

    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
  } catch (err) {
    next(err);
  }
}

module.exports = { checkout };
