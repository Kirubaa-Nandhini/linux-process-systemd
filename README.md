# Linux Process Management and systemd

## Objective
Learn how Linux processes work and how to run a Python background worker reliably using systemd.

Environment: Ubuntu 24.04 Multipass VM named `testpress`.

## Project structure

```text
linux-process-systemd/
├── app.py
├── testpress-worker.service
├── README.md
├── experiments.md
└── evidence/
```

## Installed files in the VM

- Application: `/opt/testpress-worker/app.py`
- Environment file: `/opt/testpress-worker/worker.env`
- systemd unit: `/etc/systemd/system/testpress-worker.service`

## Worker behaviour

The Python worker prints a heartbeat every five seconds. It reads:

- `HEARTBEAT_INTERVAL`: seconds between heartbeats; currently `5`.
- `CRASH_AFTER`: heartbeat count after which it exits with status 1; `0` disables the simulated crash.

It handles `SIGTERM` and `SIGINT` gracefully.

## systemd configuration

The worker runs as the dedicated non-root account `testpress-worker`.

Important settings in `/etc/systemd/system/testpress-worker.service`:

```ini
[Service]
Type=simple
User=testpress-worker
Group=testpress-worker
WorkingDirectory=/opt/testpress-worker
ExecStart=/usr/bin/python3 /opt/testpress-worker/app.py
Restart=on-failure
RestartSec=5
EnvironmentFile=/opt/testpress-worker/worker.env
CPUQuota=50%
MemoryMax=100M
```

Environment file `/opt/testpress-worker/worker.env`:

```ini
HEARTBEAT_INTERVAL=5
CRASH_AFTER=0
```

The service is enabled to start automatically at boot.

## Useful commands

Run these from Windows PowerShell:

```powershell
# VM and service status
multipass info testpress
multipass exec testpress -- sudo systemctl status testpress-worker --no-pager

# Start, stop, restart
multipass exec testpress -- sudo systemctl start testpress-worker
multipass exec testpress -- sudo systemctl stop testpress-worker
multipass exec testpress -- sudo systemctl restart testpress-worker

# Enable or disable automatic startup
multipass exec testpress -- sudo systemctl enable testpress-worker
multipass exec testpress -- sudo systemctl disable testpress-worker

# View logs
multipass exec testpress -- sudo journalctl -u testpress-worker -n 30 --no-pager
multipass exec testpress -- sudo journalctl -u testpress-worker -f

# Inspect PID and resource limits
multipass exec testpress -- sudo systemctl show testpress-worker -p MainPID
multipass exec testpress -- sudo systemctl show testpress-worker -p CPUQuotaPerSecUSec -p MemoryMax

# Validate the service file
multipass exec testpress -- sudo systemd-analyze verify /etc/systemd/system/testpress-worker.service
```

After editing the service unit, reload systemd and restart the service:

```powershell
multipass exec testpress -- sudo systemctl daemon-reload
multipass exec testpress -- sudo systemctl restart testpress-worker
```

## Key learnings

- `nohup` can keep a process running after a terminal session ends, but it does not supervise the process or restart it after failure.
- systemd supervises the worker. `Restart=on-failure` starts a new process after an unexpected failure; it does not revive the old process.
- `SIGTERM` allows graceful shutdown; `SIGKILL` terminates a process immediately.
- `journalctl` displays logs collected by journald.
- Configuring a resource limit does not by itself demonstrate what happens when that limit is exceeded. See `experiments.md`.

## Evidence

Save actual screenshots in `evidence/`. The suggested screenshot list is in `experiments.md`.
