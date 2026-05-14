def admission_threshold(queue_depth: int, service_time_ms: float) -> bool:
    """Fixture implementation used only to exercise workspace indexing."""
    return queue_depth < 64 and service_time_ms < 25.0
