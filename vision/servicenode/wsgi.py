"""Provides the Vision service node application for deployments on
WSGI-compliant web servers.

"""
from vision.servicenode.application import create_application

application = create_application()
