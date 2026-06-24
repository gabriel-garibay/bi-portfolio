CREATE SCHEMA IF NOT EXISTS core;

ALTER TABLE public.dim_customer SET SCHEMA core;
ALTER TABLE public.dim_date SET SCHEMA core;
ALTER TABLE public.dim_order SET SCHEMA core;
ALTER TABLE public.dim_product SET SCHEMA core;
ALTER TABLE public.dim_seller SET SCHEMA core;
ALTER TABLE public.fact_order_items SET SCHEMA core;
ALTER TABLE public.fact_payments SET SCHEMA core;
ALTER TABLE public.fact_reviews SET SCHEMA core;
ALTER TABLE public.geolocation SET SCHEMA core;