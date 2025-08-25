#!/usr/bin/env python3
print("=== НАЧАЛО ТЕСТА ===")
print("Python работает!")
try:
    import flask
    print("Flask успешно импортирован!")
except ImportError as e:
    print(f"Ошибка импорта Flask: {e}")
except Exception as e:
    print(f"Другая ошибка: {e}")
print("=== КОНЕЦ ТЕСТА ===")
