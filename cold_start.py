import os
import sys
from pathlib import Path
import django

# ---------------------------
# Django setup
# ---------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings
from apps.base.sys import is_windows, is_linux, is_mac

# ---------------------------
# HARD SAFETY CHECK
# ---------------------------
if not settings.DEBUG:
    print("❌ COLD START BLOCKED: DEBUG=False (Production detected)")
    sys.exit(1)

print("⚠️ WARNING: THIS WILL DELETE EVERYTHING (DB + MIGRATIONS)")
confirm = input("Type YES to continue: ")

if confirm != "YES":
    print("❌ Cancelled by user")
    sys.exit(0)

# ---------------------------
# DATABASE RESET
# ---------------------------
db = settings.DATABASES["default"]
engine = db["ENGINE"]
db_name = db["NAME"]
db_user = db.get("USER")
db_host = db.get("HOST", "127.0.0.1")
db_port = db.get("PORT", "5432")
db_password = db.get("PASSWORD")

print("🧨 Resetting database...")

if engine == "django.db.backends.sqlite3":
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"🗑️ Deleted SQLite DB: {db_name}")

elif engine == "django.db.backends.postgresql":
    os.environ["PGPASSWORD"] = db_password

    drop_cmd = f'dropdb -h {db_host} -p {db_port} -U {db_user} {db_name}'
    create_cmd = f'createdb -h {db_host} -p {db_port} -U {db_user} {db_name}'

    os.system(drop_cmd)
    os.system(create_cmd)

    print(f"🗑️ Recreated PostgreSQL DB: {db_name}")

else:
    print("❌ Unsupported database engine")
    sys.exit(1)

# ---------------------------
# DELETE MIGRATIONS
# ---------------------------
print("🧹 Deleting migrations...")

for app in settings.LOCAL_APPS:
    migrations_dir = Path(f"apps/{app}/migrations")

    if not migrations_dir.exists():
        continue

    for file in migrations_dir.iterdir():
        if file.is_file() and file.name != "__init__.py":
            file.unlink()

print("✅ Migrations cleaned")

print("✅ DATABASE AND MIGRATIONS SUCCESSFULLY DELETED")

