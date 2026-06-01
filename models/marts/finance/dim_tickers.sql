with stock_prices as (
    select * from {{ ref('int_stock_metrics') }}
),

ticker_stats as (
    select
        ticker,

        -- date range
        min(price_date)     as first_trading_date,
        max(price_date)     as last_trading_date,
        count(*)            as total_trading_days,

        -- price stats
        min(low_price)      as all_time_low,
        max(high_price)     as all_time_high,
        round(avg(close_price), 2) as avg_close_price,

        -- volume stats
        round(avg(volume), 0)      as avg_daily_volume,
        max(volume)                as max_daily_volume,

        -- return stats
        round(avg(daily_return_pct), 4)  as avg_daily_return_pct,
        round(max(daily_return_pct), 2)  as best_day_return_pct,
        round(min(daily_return_pct), 2)  as worst_day_return_pct,

        -- latest close
        max_by(close_price, price_date)          as latest_close_price,
        max_by(cumulative_return_pct, price_date) as total_return_pct

    from stock_prices
    group by ticker
),

final as (
    select
        -- surrogate key
        ticker                  as ticker_id,
        ticker,

        -- company names
        case ticker
            when 'AAPL'  then 'Apple Inc.'
            when 'GOOGL' then 'Alphabet Inc.'
            when 'MSFT'  then 'Microsoft Corporation'
            when 'AMZN'  then 'Amazon.com Inc.'
            when 'META'  then 'Meta Platforms Inc.'
        end as company_name,

        -- sector
        case ticker
            when 'AAPL'  then 'Technology'
            when 'GOOGL' then 'Communication Services'
            when 'MSFT'  then 'Technology'
            when 'AMZN'  then 'Consumer Discretionary'
            when 'META'  then 'Communication Services'
        end as sector,

        -- exchange
        'NASDAQ'                as exchange,

        -- stats
        first_trading_date,
        last_trading_date,
        total_trading_days,
        all_time_low,
        all_time_high,
        avg_close_price,
        avg_daily_volume,
        max_daily_volume,
        avg_daily_return_pct,
        best_day_return_pct,
        worst_day_return_pct,
        latest_close_price,
        total_return_pct

    from ticker_stats
)

select * from final