"""
Stub for webhook system.
Handles calling webhook URLs after parse/assignment events.
"""

def notify_webhooks(event: str, data: dict, webhook_urls: list):
    """
    Calls webhook URLs with event and data.
    Args:
        event (str): Event name.
        data (dict): Event data.
        webhook_urls (list): List of webhook URLs.
    Returns:
        list: List of responses or statuses.
    """
    # TODO: Implement real webhook notification logic
    return [] 