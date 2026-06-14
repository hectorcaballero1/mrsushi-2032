from common.jwt_helper import validate_token


def lambda_handler(event, context):
    token = event.get("authorizationToken", "")
    if token.startswith("Bearer "):
        token = token[7:]

    claims = validate_token(token)
    if not claims:
        return _policy("user", "Deny", event["methodArn"], {})

    return _policy(
        claims.get("sub", "user"),
        "Allow",
        event["methodArn"],
        {
            "userId": claims.get("sub", ""),
            "role": claims.get("role", ""),
            "tenantId": claims.get("tenantId", ""),
        },
    )


def _policy(principal_id, effect, resource, ctx):
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}],
        },
        "context": ctx,
    }
