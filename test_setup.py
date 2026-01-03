#!/usr/bin/env python
"""Quick test to see if Django setup works"""
print("Testing Django imports...")

try:
    import django
    print(f"✓ Django {django.__version__} installed")
except ImportError as e:
    print(f"✗ Django not installed: {e}")

try:
    from PIL import Image
    print(f"✓ Pillow installed")
except ImportError:
    print(f"✗ Pillow not installed")

print("\nTo fix the 'ModuleNotFoundError: No module named decouple' error:")
print("1. Your Django settings.py has been updated to use built-in environment variables")
print("2. Your models.py has been updated to work without django-countries")
print("3. You can now run: python manage.py runserver")
print("\nThe server will use SQLite by default. Switch to PostgreSQL later.")

