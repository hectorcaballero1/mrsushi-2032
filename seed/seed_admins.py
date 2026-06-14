"""
Crea un usuario admin por sede en la tabla de usuarios.
Corre desde la raíz del backend con: python -m seed.seed_admins
Requiere credenciales AWS activas (~/.aws/credentials de la sesión de AWS Academy).
"""
import os
import sys
import uuid
import boto3
from botocore.exceptions import ClientError

# Ajustar path para importar desde la raíz del backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.register import hash_password
REGION = "us-east-1"
STAGE = sys.argv[1] if len(sys.argv) > 1 else "dev"
USERS_TABLE = f"mrsushi-users-{STAGE}"

SEDES = ["mrsushi-lamarina", "mrsushi-espinar"]
PASSWORD = os.environ.get("ADMIN_SEED_PASSWORD", "admin123")

table = boto3.resource("dynamodb", region_name=REGION).Table(USERS_TABLE)

print(f"\nSeeding admins en {USERS_TABLE} ({REGION})\n{'─' * 50}")
created = []
skipped = []

for sede in SEDES:
    email = f"admin@{sede}.com"
    user_id = str(uuid.uuid4())
    item = {
        "PK": f"TENANT#{sede}",
        "SK": f"USER#{email}",
        "GSI1PK": f"USER#{user_id}",
        "userId": user_id,
        "email": email,
        "name": f"Admin {sede}",
        "role": "admin",
        "tenantId": sede,
        "passwordHash": hash_password(PASSWORD),
    }
    try:
        table.put_item(Item=item, ConditionExpression="attribute_not_exists(PK)")
        created.append((sede, email))
        print(f"  OK    {email}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            skipped.append((sede, email))
            print(f"  skip  {email} (ya existe)")
        else:
            raise

print(f"\n{'─' * 50}")
if created:
    print(f"\nCredenciales creadas (password compartida: {PASSWORD})\n")
    print(f"  {'sede':<30} {'email':<35} {'password'}")
    print(f"  {'─'*28} {'─'*33} {'─'*10}")
    for sede, email in created:
        print(f"  {sede:<30} {email:<35} {PASSWORD}")
if skipped:
    print(f"\n  Saltados (ya existían): {len(skipped)}")
print()
