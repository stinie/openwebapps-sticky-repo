try:
    from silversupport.secret import get_secret
except ImportError:
    get_secret = None
try:
    from silversupport.env import is_production
except ImportError:
    is_production = None
import os

_global_secret = None


def local_get_secret():
    global _global_secret
    if _global_secret is not None:
        return _global_secret
    secret_path = '/tmp/openwebapps-secret.txt'
    if not os.path.exists(secret_path):
        import random
        import string
        with open(secret_path, 'w') as fp:
            fp.write(''.join(
                random.choice(string.ascii_letters)
                for i in range(20)))
    fp = open(secret_path, 'rb')
    _global_secret = fp.read().strip()
    return _global_secret


def local_is_production():
    if os.environ.get('DEBUG_STICKYREPO'):
        return False
    return True


if get_secret is None:
    get_secret = local_get_secret

if is_production is None:
    is_production = local_is_production
