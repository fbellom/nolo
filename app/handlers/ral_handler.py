import time
from fastapi import Request, HTTPException
import logging


# Create Logger
logger = logging.getLogger(__name__)


# In Memory Counter
request_counters = {}


class NoloRateLimit:
    """
    Custom Rate Limit to avoid API Abuse
    """

    def __init__(
        self, requests_limit: int, time_window: int, penalty_time_in_secs: int
    ):
        self.__str__ = "Rate Limiter for API Calls"
        self.requests_limit = requests_limit
        self.time_window = time_window
        self.penalty_time = penalty_time_in_secs

    async def __call__(self, request: Request):
        client_ip = request.client.host
        route_path = request.url.path

        # Get the current timestamp
        current_time = int(time.time())

        # Create a unique key based on client IP and route path
        key = f"{client_ip}:{route_path}"

        # Check if client's request counter exists
        if key not in request_counters:
            request_counters[key] = {"timestamp": current_time, "count": 1}
        else:
            # Check if the time window has elapsed, reset the counter if needed
            if current_time - request_counters[key]["timestamp"] > (
                self.time_window + self.penalty_time
            ):
                # Reset the counter and update the timestamp
                request_counters[key]["timestamp"] = current_time
                request_counters[key]["count"] = 1
            else:
                # Check if the client has exceeded the request limit
                if request_counters[key]["count"] >= self.requests_limit:
                    logger.warning(f"Too Many Attemps from {client_ip}")
                    raise HTTPException(status_code=429, detail="Too Many Requests")
                else:
                    request_counters[key]["count"] += 1

        # Clean up expired client data (optional)
        for k in list(request_counters.keys()):
            if current_time - request_counters[k]["timestamp"] > (
                self.time_window + self.penalty_time
            ):
                request_counters.pop(k)

        return True
