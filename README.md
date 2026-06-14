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

## 2. Dependencias

```bash
pip install -r requirements.txt -t .
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
