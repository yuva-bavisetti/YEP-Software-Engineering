"""Explicit development-only reset. Existing records are never reset by seed.py."""

import argparse
from app import main as m
from seed import seed

p = argparse.ArgumentParser(
    description="Permanently delete the configured YEP database and reseed. Uploaded files are retained."
)
p.add_argument("--confirm-database", required=True)
a = p.parse_args()
if a.confirm_database != m.db.name:
    p.error("Confirmation must exactly match MONGO_DB in backend/.env")
if not m.db.name.startswith("yep"):
    p.error("Reset is limited to database names starting with yep")
m.client.drop_database(m.db.name)
seed()
