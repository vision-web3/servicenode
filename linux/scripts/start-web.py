#!/usr/bin/env python3
"""Start the service node server."""

import os
import subprocess
import sys
from importlib import resources

from vision.servicenode.configuration import config
from vision.servicenode.configuration import load_config

print('Loading the configuration...')
load_config()
print('Configuration loaded')

USER_NAME = 'vision-service-node'
APP_DIRECTORY = '/opt/vision/vision-service-node'
WSGI_FILE = str(resources.path('vision.servicenode', 'wsgi.py'))
NON_ROOT_DEFAULT_HTTPS_PORT = 8443
NON_ROOT_DEFAULT_HTTP_PORT = 8080
application_config = config['application']
host = application_config['host']
port = application_config['port']

ssl_certificate = application_config.get('ssl_certificate')
if ssl_certificate:
    ssl_private_key = application_config['ssl_private_key']
    print('SSL certificate found')

# Check if we got the --status argument
if '--status' in sys.argv:
    print('Checking the status of the server...')
    import requests
    protocol = 'https' if ssl_certificate else 'http'
    response = requests.get(f"{protocol}://{host}:{port}/health/live")
    response.raise_for_status()
    print('Server is running')
    sys.exit(0)
else:
    print('Starting the server...')

print(f'Starting the server on {host}:{port}...')
# the server should not run on a priviledged port (<1024)
if port < 1024:
    print(f'Port {port} is a privileged port, '
          'redirecting to a default port...')
    if ssl_certificate:
        default_port = NON_ROOT_DEFAULT_HTTPS_PORT
        print('SSL certificate is present, using '
              f'default HTTPS port {default_port}')
    else:
        default_port = NON_ROOT_DEFAULT_HTTP_PORT
        print('No SSL certificate present, '
              f'using default HTTP port {default_port}')
    port_redirect_command = (
        'nft add table ip nat && nft -- add chain ip nat prerouting '
        '{ type nat hook prerouting priority -100 \\; } '
        f'&& nft add rule ip nat prerouting tcp dport {port} '
        f'redirect to :{default_port}')  # noqa E203
    try:
        completed_process = subprocess.run(port_redirect_command, text=True,
                                           shell=True,
                                           check=True)  # nosec B602
        print(completed_process.stdout)
    except subprocess.CalledProcessError as error:
        if 'command not found' in error.stderr:
            print(
                'nft is not installed, unable to redirect the '
                f'port to {port}; please reinstall the package '
                f'with the recommended dependencies. {error}', file=sys.stderr)
        else:
            print(f'unable to redirect the port to {port}: {error}',
                  file=sys.stderr)
    port = default_port

# build the port command (along with the ssl certificate info if requested)
gunicorn_command = (f"python -m gunicorn --bind {host}:{port} --workers 1 "
                    "vision.servicenode.application:create_application()")
if ssl_certificate:
    gunicorn_command += (
        f" --certfile {ssl_certificate} --keyfile {ssl_private_key} ")
else:
    port_command = f'--port {port}'

server_run_command = ['runuser', '-u', USER_NAME, '--'
                      ] + gunicorn_command.split()

if os.getenv('DEV_MODE', False) == 'true':
    print('Running in development mode')
    server_run_command = server_run_command + [
        '--reload', '--log-level', 'debug'
    ]

print('Starting the server...')
subprocess.run(server_run_command, check=True, text=True)
