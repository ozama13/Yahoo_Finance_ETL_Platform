with int_metrics as (
    select * from {{ ref('int_stock_metrics') }}
),

final as (
    select
        -- surrogate key
        {{ dbt_utils.generate_surrogate_key(['price_date', 'ticker']) }} as stock_price_id,

        -- dimensions
        price_date,
        ticker,

        -- prices
        open_price,
        high_price,
        low_price,
        close_price,
        mid_price,
        price_range,
        volume,

        -- moving averages
        ma_7,
        ma_30,
        ma_90,
        avg_volume_30,

        -- signals
        daily_return_pct,
        cumulative_return_pct,
        price_vs_ma30,

        -- classify momentum signal
        case
            when close_price > ma_30 then 'above_ma30'
            when close_price < ma_30 then 'below_ma30'
            else 'at_ma30'
        end as momentum_signal,

        -- classify daily return
        case
            when daily_return_pct > 2  then 'strong_up'
            when daily_return_pct > 0  then 'up'
            when daily_return_pct = 0  then 'flat'
            when daily_return_pct > -2 then 'down'
            else 'strong_down'
        end as daily_return_category,

        loaded_at

    from int_metrics
)

select * from final