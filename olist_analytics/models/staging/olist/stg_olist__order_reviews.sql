select
    review_id,
    order_id,
    review_score::int,
    nullif(review_comment_title, '')          as review_comment_title,
    nullif(review_comment_message, '')        as review_comment_message,
    review_creation_date::timestamp,
    review_answer_timestamp::timestamp
from {{ source('bronze', 'order_reviews') }}