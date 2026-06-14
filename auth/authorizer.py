from common.jwt_helper import validate_token


def lambda_handler(event, context):
    # TODO: extraer token del header Authorization (event.authorizationToken)
    # TODO: validate_token, si es invalido => Deny
    # TODO: armar policy document Allow con context (userId, role, tenantId)
    return generate_policy("user", "Deny", event["methodArn"])


def generate_policy(principal_id, effect, resource):
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource,
                }
            ],
        },
        "context": {},
    }
