const express = require('express');

const checkoutController = require('../controllers/checkoutController');
const financialReportController = require('../controllers/financialReportController');
const userController = require('../controllers/userController');
const requireAdminKey = require('../middlewares/requireAdminKey');

const router = express.Router();

router.post('/api/checkout', checkoutController.checkout);
router.get('/api/admin/financial-report', requireAdminKey, financialReportController.financialReport);
router.delete('/api/users/:id', requireAdminKey, userController.remove);

module.exports = router;
