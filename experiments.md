# Experiments — Linux Process Management and systemd

I used my existing Multipass VM (`testpress`) to practise Linux process management and run a Python worker as a systemd service. These are the commands I tried, what happened, and a few things I learned along the way.

## 1. Running the worker in the foreground

```powershell
multipass exec testpress -- sudo -u ubuntu python3 /home/ubuntu/linux-process-systemd/app.py
```

The worker started printing a heartbeat every five seconds. When I pressed `Ctrl+C`, it received `SIGINT`, printed a shutdown message, and stopped gracefully.

## 2. Running the worker in the background

I used `nohup` to keep the worker running in the background and redirected its output to a log file.

```powershell
multipass exec testpress -- sudo -u ubuntu bash -c "cd /home/ubuntu/linux-process-systemd && nohup python3 app.py > worker.log 2>&1 < /dev/null &"
```

I checked the log using:

```powershell
multipass exec testpress -- sudo -u ubuntu tail -n 5 /home/ubuntu/linux-process-systemd/worker.log
```

The heartbeat messages appeared in the log even after the command returned to the terminal. This helped me understand how `nohup` and output redirection work.

## 3. Checking running processes

I tried a few commands to find and inspect running processes.

```bash
ps aux
pgrep -af "python3 app.py"
ps -o pid,ppid,cmd -p <PID>
```

I learned how to find a process, check its PID and parent PID, and view the command used to start it.

## 4. Stopping the worker through systemd

I used systemd to stop the worker instead of killing the process directly.

```powershell
multipass exec testpress -- sudo systemctl stop testpress-worker
multipass exec testpress -- sudo journalctl -u testpress-worker -n 8 --no-pager
```

The logs showed that the worker received `SIGTERM` (signal 15) and shut down gracefully. I started the service again using `systemctl start`.

## 5. Checking automatic restart after a crash

I temporarily changed `CRASH_AFTER` to `3` in the environment file to make the worker exit after a few heartbeats.

After restarting the service, I checked its logs:

```powershell
multipass exec testpress -- sudo journalctl -u testpress-worker -n 25 --no-pager
```

The worker crashed with exit status 1, and systemd started it again after the configured delay. I changed `CRASH_AFTER` back to `0` after the test.

This helped me understand how `Restart=on-failure` works.

## 6. Checking recovery after SIGKILL

I also tried forcefully terminating the worker process.

```powershell
multipass exec testpress -- sudo systemctl show testpress-worker -p MainPID
multipass exec testpress -- sudo kill -KILL <PID>
```

After waiting a few seconds, I checked the service again:

```powershell
multipass exec testpress -- sudo systemctl status testpress-worker --no-pager
```

The original process was terminated, but systemd started a new one. I verified that the service was running with a different PID.

## 7. Using an environment file

I created an environment file at `/opt/testpress-worker/worker.env` to keep the worker's configuration separate from the application code.

```ini
HEARTBEAT_INTERVAL=5
CRASH_AFTER=0
```

I added the following setting to the systemd service:

```ini
EnvironmentFile=/opt/testpress-worker/worker.env
```

I reloaded systemd, restarted the service, and checked that it recognised the environment file.

## 8. Setting CPU and memory limits

I added these limits to the service configuration:

```ini
CPUQuota=50%
MemoryMax=100M
```

After reloading systemd and restarting the service, I checked the configured limits:

```powershell
multipass exec testpress -- sudo systemctl show testpress-worker -p CPUQuotaPerSecUSec -p MemoryMax
```

The CPU quota was set to 50%, and the memory limit was set to 100 MB. The worker was using approximately 4.1 MB of memory at the time of checking.

I verified the configuration but did not try to make the worker exceed the memory limit.

## 9. Starting the service automatically after reboot

I enabled the service so that it would start automatically when the VM boots.

```powershell
multipass exec testpress -- sudo systemctl enable testpress-worker
multipass exec testpress -- sudo reboot
```

After the VM restarted, I checked the service:

```powershell
multipass exec testpress -- sudo systemctl status testpress-worker --no-pager
```

The worker was running again without me having to start it manually.

## Screenshots

The following screenshots are included as evidence of the main experiments:

1. `01-foreground-worker.png` — Worker heartbeats and graceful shutdown using Ctrl+C.
2. `02-nohup-background.png` — Worker running in the background and writing to a log file.
3. `04-systemd-status.png` — systemd service status, including its running state and process details.
4. `06-crash-restart.png` — Worker crash and automatic restart by systemd.