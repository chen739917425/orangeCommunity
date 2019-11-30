from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from flask import current_app
def generate_token(payload,expiration):
    token=Serializer(
        secret_key=current_app.config['SECRET_KEY'],
        salt=current_app.config['SALT'],
        expires_in=expiration
    )
    return token.dumps(payload)

def verify_token(token):
    s=Serializer(secret_key=current_app.config['SECRET_KEY'],salt=current_app.config['SALT'])
    try:
        data=s.loads(token)
    except SignatureExpired:
        return None
    except BadSignature:
        return None
    except:
        return None
    return data


