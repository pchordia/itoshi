# Gunicorn configuration file for production deployment

import multiprocessing
import os

# Bind to localhost (nginx will proxy)
bind = "127.0.0.1:8000"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"

# Connections
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeouts
timeout = 300  # 5 minutes for long-running AI requests
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "gunicorn-access.log")
errorlog = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "gunicorn-error.log")
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "itoshi_web_app"

# Server mechanics
daemon = False
pidfile = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "gunicorn.pid")
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if terminating SSL at gunicorn instead of nginx)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Server hooks
def on_starting(server):
    print("Gunicorn server is starting...")

def on_reload(server):
    print("Gunicorn server is reloading...")

def when_ready(server):
    print(f"Gunicorn server is ready. Spawning {workers} workers.")

def on_exit(server):
    print("Gunicorn server is shutting down...")

