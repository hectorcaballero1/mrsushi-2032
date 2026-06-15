from common.jwt_helper import validate_token


def lambda_handler(event, context):
    token = event.get("authorizationToken", "")
    if token.startswith("Bearer "):
        token = token[7:]

    # Wildcard ARN: permite todos los endpoints del stage con el mismo token cacheado
    arn_parts = event["methodArn"].split(":")
    region, account = arn_parts[3], arn_parts[4]
    api_id, stage = arn_parts[5].split("/")[:2]
    wildcard_arn = f"arn:aws:execute-api:{region}:{account}:{api_id}/{stage}/*/*"

    claims = validate_token(token)
    if not claims:
        return _policy("user", "Deny", wildcard_arn, {})

    return _policy(
        claims.get("sub", "user"),
        "Allow",
        wildcard_arn,
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
