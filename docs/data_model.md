# Modelo dimensional

## Grão

`marts.fct_sales` contém uma linha para cada `order_item_id`. O grão é declarado antes das métricas para evitar somas duplicadas ao combinar pedidos e produtos.

## Dimensões

### `dim_customer`

Uma linha por cliente atual. `customer_sk` é uma chave substituta determinística criada por hash do identificador de negócio. O histórico completo fica em `snapshots.customers_snapshot`.

### `dim_product`

Uma linha por produto, contendo categoria, subcategoria, preço de lista, custo e status de atividade.

### `dim_date`

Uma linha por dia entre o menor e o maior pedido, com ano, trimestre, mês, semana, dia da semana e indicador de fim de semana.

## Tabela fato

| Coluna | Semântica |
|---|---|
| `sales_sk` | chave substituta da linha de venda |
| `order_item_id` | chave natural e unique key incremental |
| `order_id` | dimensão degenerada do pedido |
| `date_key` | relacionamento com calendário |
| `customer_sk` | relacionamento com cliente |
| `product_sk` | relacionamento com produto |
| `quantity` | unidades da linha |
| `gross_sales_amount` | quantidade × preço unitário |
| `discount_amount` | desconto monetário calculado |
| `net_sales_amount` | bruto menos desconto |
| `cost_amount` | quantidade × custo unitário |
| `margin_amount` | venda líquida menos custo |
| `recognized_revenue` | venda líquida quando entregue |
| `returned_amount` | venda líquida quando devolvida |
| `source_updated_at` | watermark da carga incremental |

## Chaves substitutas

Hashes MD5 são usados apenas como chaves técnicas determinísticas do warehouse, não para segurança. Isso mantém as chaves estáveis entre execuções e desacopla os fatos dos identificadores operacionais.

## Slowly Changing Dimension

`customers_snapshot` usa estratégia `timestamp` sobre `updated_at`. O dbt adiciona `dbt_valid_from`, `dbt_valid_to` e metadados de versão, preservando alterações de segmento ou localização ao longo do tempo.
