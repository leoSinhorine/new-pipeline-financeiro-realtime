{{ config(
    materialized='table',
    partition_by={
      "field": "data_referencia",
      "data_type": "date",
      "granularity": "day"
    },
    cluster_by=["codigo_moeda"]
) }}

with usd as (
    select
        cast(data_hora as date) as data_referencia,
        data_hora,
        'USD' as codigo_moeda,
        'Dólar Americano' as nome_moeda,
        cotacao_compra,
        cotacao_venda
    from {{ ref('stg_usd_brl') }}
),

eur as (
    select
        cast(data_hora as date) as data_referencia,
        data_hora,
        'EUR' as codigo_moeda,
        'Euro' as nome_moeda,
        cotacao_compra,
        cotacao_venda
    from {{ ref('stg_eur_brl') }}
),

btc as (
    select
        cast(data_hora as date) as data_referencia,
        data_hora,
        'BTC' as codigo_moeda,
        'Bitcoin' as nome_moeda,
        cotacao_compra,
        cotacao_venda
    from {{ ref('stg_btc_brl') }}
),

unificados as (
    select * from usd
    union all
    select * from eur
    union all
    select * from btc
),

fatos_com_chaves as (
    select
        -- Geramos uma chave primária surrogate (hash MD5) exclusiva para cada registro consolidado
        generate_uuid() as cotacao_key,
        data_referencia,
        data_hora,
        codigo_moeda,
        nome_moeda,
        cotacao_compra,
        cotacao_venda,
        -- Métrica de Spread (diferença entre venda e compra)
        (cotacao_venda - cotacao_compra) as spread,
        current_timestamp() as carregado_em
    from unificados
)

select * from fatos_com_chaves