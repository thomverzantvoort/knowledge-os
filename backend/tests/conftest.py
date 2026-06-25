import os

import bcrypt

if "AUTH_USERNAME" not in os.environ:
    os.environ["AUTH_USERNAME"] = "test"
if "AUTH_PASSWORD_HASH" not in os.environ:
    _hash = bcrypt.hashpw(b"test", bcrypt.gensalt()).decode("utf-8")
    os.environ["AUTH_PASSWORD_HASH"] = _hash
if "JWT_SECRET" not in os.environ:
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only"
