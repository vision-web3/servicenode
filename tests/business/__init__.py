from unittest.mock import patch

with patch('vision.servicenode.configuration.config'):
    import vision.servicenode.celery  # noqa: F401
