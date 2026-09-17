CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]

STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

# (limite de faturamento, taxa de desconto aplicável), avaliados em ordem decrescente
DESCONTO_TIERS = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)
