from collections.abc import Callable
from datetime import datetime

Clock = Callable[[], datetime]
"""Returns the current timezone-aware (UTC) time."""
