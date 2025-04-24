from werkzeug.security import generate_password_hash, check_password_hash

pwd = "qwerty12"

hashed = generate_password_hash(pwd, method='pbkdf2:sha256', salt_length=16)


if check_password_hash(hashed, "qwerty12"):
    print("same")
else:
    print("false my nigga!")