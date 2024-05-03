"""This module contains configuration constants used across the framework"""

from datetime import datetime

# The number of times the robot retries on an error before terminating.
MAX_RETRY_COUNT = 3

# Whether the robot should be marked as failed if MAX_RETRY_COUNT is reached.
FAIL_ROBOT_ON_TOO_MANY_ERRORS = True

# Error screenshot config
SMTP_SERVER = "smtp.aarhuskommune.local"
SMTP_PORT = 25
SCREENSHOT_SENDER = "robot@friend.dk"

# Constant/Credential names
ERROR_EMAIL = "Error Email"
GRAPH_API = "Graph api"
EFLYT_CREDS = "Eflyt"
NOVA_CREDS = "Mathias KMD"
NOVA_API = "Nova API"

QUEUE_NAME = "Folkeregisterbøder"

FINE_RATES = (
    (datetime(2024, 1, 1), 945),
    (datetime(2023, 1, 1), 900),
    (datetime(2023, 1, 1), 580),
    (datetime(2022, 1, 1), 570),
    (datetime(2021, 1, 1), 560),
    (datetime(2020, 1, 1), 550),
    (datetime(1900, 1, 1), 500)
)
