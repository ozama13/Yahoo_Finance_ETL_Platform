with source as (
    select * from {{ source('yahoo_finance', 'stock_prices') }}
),

cleaned as (
    select
        -- keys
        date                            as price_date,
        ticker,

        -- prices (rounded to 2 decimal places)
        round(open, 2)                  as open_price,
        round(high, 2)                  as high_price,
        round(low, 2)                   as low_price,
        round(close, 2)                 as close_price,

        -- volume
        volume,

        -- daily price range
        round(high - low, 2)            as price_range,

        -- mid price
        round((high + low) / 2, 2)      as mid_price,

        -- metadata
        loaded_at

    from source
    where close is not null
        and volume > 0
)

select * from cleaned