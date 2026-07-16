{{ config(
    materialized='table',
    partition_by={
      "field": "data_referencia",
      "data_type": "date",
      "granularity": "day"
    },
    cluster_by=["codigo_moeda"]
) }}

with fatos as (
    select * from {{ ref('fct_cotacoes') }}
),

dim_tempo as (
    select * from {{ ref('dim_tempo') }}
),

-- 1. Juntamos os dados das cotações com os atributos ricos do calendário
fatos_enriquecidos as (
    select
        f.cotacao_key,
        f.data_referencia,
        f.data_hora,
        f.codigo_moeda,
        f.nome_moeda,
        f.cotacao_compra,
        f.cotacao_venda,
        f.spread,
        t.ano,
        t.mes,
        t.nome_mes,
        t.nome_dia_semana,
        t.eh_fim_semana
    from fatos f
    left join dim_tempo t
        on f.data_referencia = t.data_dia
),

-- 2. Calculamos as métricas de variação e médias móveis usando funções de janela (Window Functions)
calculo_kpis as (
    select
        *,
        -- Cotação do dia anterior para calcular a variação
        lag(cotacao_compra) over(
            partition by codigo_moeda 
            order by data_referencia
        ) as cotacao_dia_anterior,

        -- Média móvel de 7 dias
        avg(cotacao_compra) over(
            partition by codigo_moeda 
            order by data_referencia
            rows between 6 preceding and current row
        ) as media_movel_7_dias,

        -- Média móvel de 30 dias
        avg(cotacao_compra) over(
            partition by codigo_moeda 
            order by data_referencia
            rows between 29 preceding and current row
        ) as media_movel_30_dias
    from fatos_enriquecidos
),

-- 3. Finalizamos calculando a variação percentual com tratamento para divisão por zero
metricas_finais as (
    select
        cotacao_key,
        data_referencia,
        data_hora,
        codigo_moeda,
        nome_moeda,
        cotacao_compra,
        cotacao_venda,
        spread,
        ano,
        mes,
        nome_mes,
        nome_dia_semana,
        eh_fim_semana,
        round(media_movel_7_dias, 4) as media_movel_7_dias,
        round(media_movel_30_dias, 4) as media_movel_30_dias,
        
        -- Cálculo da variação diária em % (ex: 1.5 para +1.5% ou -0.8 para -0.8%)
        case 
            when cotacao_dia_anterior is null or cotacao_dia_anterior = 0 then 0.0
            else round(((cotacao_compra - cotacao_dia_anterior) / cotacao_dia_anterior) * 100, 2)
        end as variacao_diaria_pct
    from calculo_kpis
)

select * from metricas_finais