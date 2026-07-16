{{ config(
    materialized='table',
    partition_by={
      "field": "data_dia",
      "data_type": "date",
      "granularity": "day"
    }
) }}

with datas_geradas as (
    -- Geramos uma sequência diária de datas desde o início de 2024 até o final de 2026
    select data_dia
    from unnest(
        generate_date_array('2024-01-01', '2026-12-31', interval 1 day)
    ) as data_dia
),

atributos_data as (
    select
        data_dia,
        extract(year from data_dia) as ano,
        extract(month from data_dia) as mes,
        extract(day from data_dia) as dia,
        extract(quarter from data_dia) as trimestre,
        
        -- Nomes e formatações em português para facilitar o BI
        format_date('%B', data_dia) as nome_mes,
        format_date('%A', data_dia) as nome_dia_semana,
        
        -- Identificadores numéricos para ordenação no dashboard
        extract(dayofweek from data_dia) as dia_semana_num,
        extract(isoyear from data_dia) as ano_iso,
        extract(isoweek from data_dia) as semana_ano_num,
        
        -- Flag para identificar finais de semana
        case 
            when extract(dayofweek from data_dia) in (1, 7) then true 
            else false 
        end as eh_fim_semana
    from datas_geradas
)

select * from atributos_data