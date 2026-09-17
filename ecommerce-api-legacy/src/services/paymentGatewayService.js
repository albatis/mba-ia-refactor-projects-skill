// Mock de gateway de pagamento para fins de demonstração — não processa pagamentos
// reais. Isolar essa decisão aqui (em vez de inline no meio do fluxo de checkout)
// torna a regra testável isoladamente e substituível por uma integração real sem
// tocar no controller.

function maskCard(cardNumber) {
  return cardNumber.replace(/\d(?=\d{4})/g, '*');
}

function authorize(cardNumber) {
  console.log(`Autorizando pagamento para cartão ${maskCard(cardNumber)}`);
  const approved = cardNumber.startsWith('4');
  return { status: approved ? 'PAID' : 'DENIED' };
}

module.exports = { authorize, maskCard };
