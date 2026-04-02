import os
from logging import basicConfig

import logfire

logfire.configure(
    token=os.getenv("LOGFIRE_TOKEN"),
    service_name="polarization-review",
    service_version="0.1.0",
    environment=os.getenv("APP_ENV", "development"),
    send_to_logfire="if-token-present",
    min_level="debug",
    console=logfire.ConsoleOptions(
        colors="auto",
        span_style="indented",
        include_timestamps=True,
        verbose=True,
        min_log_level="debug",
    ),
    scrubbing=logfire.ScrubbingOptions(
        extra_patterns=["api_key", "token", "secret"],
    ),
)

# Bridge: routes all standard logger.warning/info/debug calls to logfire
basicConfig(handlers=[logfire.LogfireLoggingHandler()])
