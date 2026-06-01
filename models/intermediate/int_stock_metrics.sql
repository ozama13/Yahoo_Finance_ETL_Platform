with stg as (
    select * from {{ ref('stg_stock_prices') }}
),

with_metrics as (
    select
        price_date,
        ticker,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        price_range,
        mid_price,

        -- daily return vs previous trading day
        round(
            (close_price - lag(close_price) over (
                partition by ticker order by price_date
            )) / nullif(lag(close_price) over (
                partition by ticker order by price_date
            ), 0) * 100,
        2) as daily_return_pct,

        -- 7-day moving average
        round(avg(close_price) over (
            partition by ticker
            order by price_date
            rows between 6 preceding and current row
        ), 2) as ma_7,

        -- 30-day moving average
        round(avg(close_price) over (
            partition by ticker
            order by price_date
            rows between 29 preceding and current row
        ), 2) as ma_30,

        -- 90-day moving average
        round(avg(close_price) over (
            partition by ticker
            order by price_date
            rows between 89 preceding and current row
        ), 2) as ma_90,

        -- 30-day rolling volume average
        round(avg(volume) over (
            partition by ticker
            order by price_date
            rows between 29 preceding and current row
        ), 0) as avg_volume_30,

        -- price vs 30-day moving average (momentum signal)
        round(close_price - avg(close_price) over (
            partition by ticker
            order by price_date
            rows between 29 preceding and current row
        ), 2) as price_vs_ma30,

        -- cumulative return from start date
        round(
            (close_price - first_value(close_price) over (
                partition by ticker order by price_date
            )) / nullif(first_value(close_price) over (
                partition by ticker order by price_date
            ), 0) * 100,
        2) as cumulative_return_pct,

        loaded_at

    from stg
)

select * from with_metrics