#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/kotaro/code/IS_RE_engineering/USER_service')

from app.utils.hasher import hash_password

# Сгенерировать хеш для Test123456!
new_hash = hash_password('Test123456!')
print('Новый хеш для Test123456!:', new_hash)

# Сгенерировать хеш для test123
simple_hash = hash_password('test123')
print('Хеш для test123:', simple_hash)

# Сгенерировать хеш для admin123
admin_hash = hash_password('admin123')
print('Хеш для admin123:', admin_hash)
