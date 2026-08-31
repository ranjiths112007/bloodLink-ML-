"""Gunicorn entrypoint: initialize application state before workers serve traffic."""
import os

from app import app, init_db

# Never seed demo records in production. Real deployments must provision
# verified donor data separately.
init_db(seed_demo=os.getenv("BLOODLINK_ENV", "development") != "production")
