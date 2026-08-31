"""Gunicorn entrypoint: initialize application state before workers serve traffic."""
import os

from app import app, init_db

# Demo deployments can opt into the bundled synthetic Tamil Nadu donor dataset.
# Production systems should set BLOODLINK_SEED_DEMO=false and provision verified data.
seed_demo = os.getenv("BLOODLINK_SEED_DEMO", "true").strip().lower() in {"1", "true", "yes", "on"}
init_db(seed_demo=seed_demo)
