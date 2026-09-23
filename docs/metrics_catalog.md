# Catálogo de métricas

| Métrica | Definição | Fonte |
|---|---|---|
| Pedidos | contagem distinta de `order_id` | `fct_sales` |
| Clientes ativos | clientes distintos com pedido | `fct_sales` |
| Unidades | soma de `quantity` | `fct_sales` |
| Vendas brutas | quantidade × preço antes do desconto | `gross_sales_amount` |
| Desconto | valor monetário concedido | `discount_amount` |
| Venda líquida | venda bruta menos desconto | `net_sales_amount` |
| Receita reconhecida | venda líquida de pedidos entregues | `recognized_revenue` |
| Valor devolvido | venda líquida de pedidos devolvidos | `returned_amount` |
| Margem reconhecida | venda líquida menos custo em pedidos entregues | `margin_amount` |
| Ticket médio entregue | receita reconhecida ÷ pedidos entregues | marts diário/canal |
| Recência | última data global menos última compra do cliente | `mart_customer_360` |
| Tier do cliente | faixa de receita vitalícia | `mart_customer_360` |

## Regras de status

- `Delivered`: receita reconhecida e margem reconhecida;
- `Shipped` e `Processing`: venda registrada, ainda sem reconhecimento;
- `Cancelled`: preservado para análise operacional, sem receita;
- `Returned`: registrado separadamente como valor devolvido.

## Moeda

Os valores representam reais brasileiros no cenário demonstrativo. Não há conversão cambial; `country` indica o mercado do pedido, não sua moeda de origem.
