with ranked as (
    select
        order_id,
        review_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date,
        review_answer_timestamp,
        row_number() over (
            partition by order_id
            order by review_answer_timestamp desc
        ) as rn
    from {{ ref('stg_olist__order_reviews') }}
)

select
    order_id,
    review_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date,
    review_answer_timestamp
from ranked
where rn = 1