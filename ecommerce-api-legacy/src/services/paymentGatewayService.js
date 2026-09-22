// Mock de gateway de pagamento para fins de demonstração — não processa pagamentos
// reais. Isolar essa decisão aqui (em vez de inline no meio do fluxo de checkout)
// torna a regra testável isoladamente e substituível por uma integração real sem
// tocar no controller.
//
// A aprovação é deliberadamente restrita a uma lista fechada de cartões de teste
// documentados (padrão comum em gateways reais, ex.: o cartão de teste "4242...").
// Uma regra genérica como "aprova se começar com 4" seria trivialmente descoberta
// e manipulada por qualquer chamador — qualquer cartão real ou inventado com esse
// prefixo passaria. Deny-by-default: só os números abaixo são aprovados.
const logger = require('../utils/logger');

const APPROVED_TEST_CARDS = new Set([
  '4242424242424242', // cartão de teste "sempre aprova" (documentado no README/api.http)
  '4000056655665556', // segundo cartão de teste "sempre aprova"
]);

function maskCard(cardNumber) {
  return cardNumber.replace(/\d(?=\d{4})/g, '*');
}

function authorize(cardNumber) {
  logger.info(`Autorizando pagamento para cartão ${maskCard(cardNumber)}`);
  const approved = APPROVED_TEST_CARDS.has(cardNumber);
  return { status: approved ? 'PAID' : 'DENIED' };
}

module.exports = { authorize, maskCard };
