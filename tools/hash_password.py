import sys
import getpass
import os
import hashlib

def main():
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass("Enter administrator password to hash: ")
        confirm = getpass.getpass("Confirm administrator password: ")
        if password != confirm:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)
            
    if not password:
        print("Error: Password cannot be empty.", file=sys.stderr)
        sys.exit(1)

    try:
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash(password)
    except ImportError:
        # Standard library fallback: generates Werkzeug-compatible PBKDF2 hash
        salt = os.urandom(16).hex()
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 600000).hex()
        hashed = f"pbkdf2:sha256:600000${salt}${key}"

    print("\nCopy and paste this hash into your .env file as ADMIN_PASSWORD_HASH:\n")
    print(hashed)
    print()

if __name__ == "__main__":
    main()
