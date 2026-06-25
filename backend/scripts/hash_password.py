import sys

import bcrypt


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run python scripts/hash_password.py <password>")
        sys.exit(1)

    password = sys.argv[1]
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    print(hashed.decode("utf-8"))


if __name__ == "__main__":
    main()
