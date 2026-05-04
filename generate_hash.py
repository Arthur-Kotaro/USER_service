# generate_hash.py
import bcrypt

password = "yrjIehJ648_hA1-sk"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

print(f"Password: {password}")
print(f"Hash: {hashed.decode('utf-8')}")
