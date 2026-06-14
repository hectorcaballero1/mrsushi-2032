# mrsushi-2032

API REST serverless para Mr Sushi.

## 1. Variables de entorno

Copia `.env.example` y completa los valores:

```bash
cp .env.example .env
```

| Variable | Descripción |
|---|---|
| `AWS_ACCOUNT_ID` | ID cuenta AWS Academy |
| `SLS_ORG` | Org de Serverless Framework |
| `JWT_SECRET` | Secreto para firmar/verificar JWT |
| `RAPPI_API_URL` | URL base de la API Rappi |
| `RAPPI_WEBHOOK_SECRET` | Secreto compartido con la API Rappi |

Carga las variables en la sesión antes de cualquier comando:

```bash
export $(grep -v '^#' .env | xargs)
```

## 2. Entorno virtual y dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Deploy

### Infraestructura (tablas, bucket, event bus)

```bash
serverless deploy --config resources.yml
```

### Plataforma (funciones, state machine, regla EventBridge)

```bash
serverless deploy
```

Primero `resources.yml`, luego `serverless.yml`.

## 4. Seed

### Admins

```bash
python -m seed.seed_admins dev
```

### Catálogo (productos + imágenes)

Requiere que `resources.yml` ya esté desplegado (bucket S3 + tabla `mrsushi-products-<stage>`).

```bash
python seed/scrape.py       # genera seed/catalog.json + seed/images/
python -m seed.seed_catalog dev     # sube imágenes a S3 y escribe productos en DynamoDB
```

Re-correr sobreescribe sin condición.

## Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| POST | `/auth/register` | — | Registro de usuario |
| POST | `/auth/login` | — | Login, devuelve JWT |
| GET | `/products` | — | Catálogo completo |
| POST | `/orders` | — | Crear pedido (web o Rappi) |
| GET | `/orders` | JWT | Listar pedidos del tenant |
| GET | `/orders/{id}` | JWT | Obtener pedido |
| POST | `/orders/{id}/advance` | JWT | Avanzar paso del workflow |
| GET | `/dashboard` | JWT (admin) | Stats por status |
| POST | `/webhooks/rappi/delivered` | API key | Callback de entrega Rappi |
