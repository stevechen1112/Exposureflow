"""Registered background job types for ExposureFlow."""

JOB_DEFINITIONS: list[dict[str, str | int | bool | None]] = [
    {
        "job_type": "gsc.sync",
        "description": "Incremental Google Search Console sync",
        "default_schedule": "0 2 * * *",
        "enabled": True,
        "max_retries": 3,
    },
    {
        "job_type": "ga4.sync",
        "description": "GA4 page metrics sync",
        "default_schedule": "0 3 * * *",
        "enabled": True,
        "max_retries": 3,
    },
    {
        "job_type": "serp.snapshot",
        "description": "SERP matrix snapshot collection",
        "default_schedule": None,
        "enabled": True,
        "max_retries": 2,
    },
    {
        "job_type": "tech_seo.crawl",
        "description": "Technical SEO crawl",
        "default_schedule": "0 4 * * 0",
        "enabled": True,
        "max_retries": 2,
    },
    {
        "job_type": "bing.sync",
        "description": "Bing Webmaster Tools incremental sync",
        "default_schedule": "0 5 * * *",
        "enabled": True,
        "max_retries": 3,
    },
    {
        "job_type": "integration.health_check",
        "description": "Integration connectivity health check",
        "default_schedule": "0 6 * * *",
        "enabled": True,
        "max_retries": 2,
    },
    {
        "job_type": "exposure.aggregate",
        "description": "Exposure core daily aggregation",
        "default_schedule": "0 1 * * *",
        "enabled": True,
        "max_retries": 3,
    },
]
