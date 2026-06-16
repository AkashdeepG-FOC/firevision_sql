import math

class RetryHandler:
    """Calculates exponential backoff for failed sync attempts."""
    
    BASE_DELAY_SECONDS = 5
    MAX_DELAY_SECONDS = 300 # 5 minutes max
    
    @staticmethod
    def get_backoff_delay(retry_count: int) -> float:
        """
        Calculate backoff delay using exponential strategy.
        0 retries -> 0s
        1 retry -> 5s
        2 retries -> ~15s (varies based on base)
        Formula: base * (2 ^ (retry - 1))
        """
        if retry_count <= 0:
            return 0.0
            
        delay = RetryHandler.BASE_DELAY_SECONDS * math.pow(2, retry_count - 1)
        return min(delay, float(RetryHandler.MAX_DELAY_SECONDS))
        
    @staticmethod
    def should_retry_now(last_attempt_time: float, retry_count: int, current_time: float) -> bool:
        """Determine if enough time has passed to retry based on backoff."""
        if retry_count == 0:
            return True
            
        required_delay = RetryHandler.get_backoff_delay(retry_count)
        return (current_time - last_attempt_time) >= required_delay
