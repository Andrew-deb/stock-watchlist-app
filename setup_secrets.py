"""
One-time setup script: creates the Databricks secret scope and stores the
Massive API key. Run this locally (with the Databricks CLI configured) or
from a notebook - never commit the resulting secret value anywhere.

Usage:
    python setup_secrets.py
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import workspace
from databricks.sdk.errors import ResourceAlreadyExists
import getpass

w = WorkspaceClient()

# Helper function to create scope if it doesn't exist
def create_scope_if_not_exists(scope_name):
    try:
        w.secrets.create_scope(scope=scope_name)
        print(f"✅ Created scope: {scope_name}")
    except ResourceAlreadyExists:
        print(f"ℹ️  Scope '{scope_name}' already exists, skipping creation")

# Create scopes (or skip if they exist)
create_scope_if_not_exists("massive")
create_scope_if_not_exists("database")

# Add secrets
print("\n📝 Setting up secrets...")
w.secrets.put_secret(
    scope="massive",
    key="api-key",
    string_value=getpass.getpass("Paste your Massive API key: ")
)
print("✅ Massive API key stored")

w.secrets.put_secret(
    scope="database",
    key="lakebase-url",
    string_value=getpass.getpass("Paste your Lakebase URL: ")
)
print("✅ Lakebase URL stored")

# Set ACL permissions
print("\n🔐 Setting permissions...")
w.secrets.put_acl(
    scope="database",
    principal="users",
    permission=workspace.AclPermission.READ,
)
print("✅ Database scope permissions set")

w.secrets.put_acl(
    scope="massive",
    principal="users",
    permission=workspace.AclPermission.READ,
)
print("✅ Massive scope permissions set")

print("\n🎉 Setup complete! Your secrets are ready to use.")
