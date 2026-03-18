import os

import logfire

token = os.getenv("LOGFIRE_TOKEN")
logfire.configure(token=token)
