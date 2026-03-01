import os

# Run all tests with ENV=test so config reads API keys from env vars
# instead of nulling them out (which is the behaviour for ENV=local).
os.environ.setdefault("ENV", "test")
