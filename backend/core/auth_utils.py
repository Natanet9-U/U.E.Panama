from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner


def get_signer():
    salt = getattr(settings, "AUTH_TOKEN_SALT", "ue.panama.auth")
    return TimestampSigner(salt=salt)


def build_token(user_id):
    signer = get_signer()
    return signer.sign(str(user_id))


def decode_token(token):
    signer = get_signer()
    max_age = getattr(settings, "AUTH_TOKEN_MAX_AGE", 60 * 60 * 24)

    try:
        user_id = signer.unsign(token, max_age=max_age)
        return user_id, None
    except SignatureExpired:
        return None, "TOKEN_EXPIRED"
    except BadSignature:
        return None, "TOKEN_INVALID"
