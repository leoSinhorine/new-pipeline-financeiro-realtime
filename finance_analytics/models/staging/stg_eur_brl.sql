with source_data as (
    select * from {{ source('raw', 'raw_eurbrl') }}
),

renamed as (
    select
        parse_timestamp('%Y-%m-%dT%H:%M:%S', split(timestamp, '.')[offset(0)]) as data_hora,
        moeda as par_moeda,
        cast(bid as float64) as cotacao_compra,
        cast(ask as float64) as cotacao_venda
    from source_data
    where bid is not null
)

select * from renamed