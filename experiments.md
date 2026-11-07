# Experiments — Linux Process Management and systemd

This document records the practical work completed and distinguishes tested items from items that remain to be demonstrated. Commands were run from Windows PowerShell against the Multipass VM `testpress`, unless noted otherwise.

## 1. Foreground worker and graceful Ctrl+C

**Command:**

```powershell
multipass exec testpress -- sudo -u ubuntu python3 /home/ubuntu/linux-process-systemd/app.py
```

**Observed:** Heartbeats appeared every five seconds. Ctrl+C delivered `SIGINT`; the worker printed its graceful-shutdown message and exited.

**Status:** Tested.

## 2. Background worker with nohup

**Command:**

```powershell
multipass exec testpress -- sudo -u ubuntu bash -c "cd /home/ubuntu/linux-process-systemd && nohup python3 app.py > worker.log 2>&1 < /dev/null &"
```

**Verification:**

```powershell
multipass exec testpress -- sudo -u ubuntu tail -n 5 /home/ubuntu/linux-process-systemd/worker.log
```

**Observed:** Heartbeat messages appeared in `worker.log`, confirming output redirection.

**Status:** Tested. Temporary background processes were stopped before using the systemd-managed worker.

## 3. Process inspection

**Commands practised:**

```bash
ps aux
pgrep -af "python3 app.py"
ps -o pid,ppid,cmd -p <PID>
```

**Observed:** `ps` displayed process details, `pgrep` found matching processes, and `ps -o` selected PID, parent PID, and command columns.

**Status:** Practised.

## 4. Graceful shutdown through systemd

**Commands:**

```powershell
multipass exec testpress -- sudo systemctl stop testpress-worker
multipass exec testpress -- sudo journalctl -u testpress-worker -n 8 --no-pager
```

**Observed:** The journal showed signal 15 (`SIGTERM`), the worker's graceful-shutdown message, and a successful service stop. The service was started again with `systemctl start`.

**Status:** Tested.

## 5. Restart after application crash

For this test, `CRASH_AFTER` was temporarily set to `3`. The service was reloaded and restarted.

**Verification:**

```powershell
multipass exec testpress -- sudo systemctl status testpress-worker --no-pager
multipass exec testpress -- sudo journalctl -u testpress-worker -n 25 --no-pager
```

**Observed:** The journal showed the simulated crash, exit status 1, a scheduled restart, and a new worker process. `CRASH_AFTER` was restored to `0` afterwards.

**Status:** Tested.

## 6. Recovery after SIGKILL

**Commands:**

```powershell
multipass exec testpress -- sudo systemctl show testpress-worker -p MainPID
multipass exec testpress -- sudo kill -KILL <PID>
Start-Sleep -Seconds 7
multipass exec testpress -- sudo systemctl status testpress-worker --no-pager
```

Replace `<PID>` with the `MainPID` returned by the first command.

**Observed:** The original process was forcefully terminated. systemd started a new worker. The new process was observed running with PID `7349`.

**Status:** Tested.

## 7. Environment file

Environment file: `/opt/testpress-worker/worker.env`

```ini
HEARTBEAT_INTERVAL=5
CRASH_AFTER=0
```

The service unit uses:

```ini
EnvironmentFile=/opt/testpress-worker/worker.env
```

After editing the unit, systemd was reloaded and the service restarted.

**Verification:**

```powershell
multipass exec testpress -- sudo systemctl show testpress-worker -p EnvironmentFiles
```

**Observed:** systemd reported `/opt/testpress-worker/worker.env` as the service's environment file.

**Status:** Configured and verified.

## 8. CPU and memory limits

The service unit includes:

```ini
CPUQuota=50%
MemoryMax=100M
```

After reloading systemd and restarting the service, the limits were checked with:

```powershell
multipass exec testpress -- sudo systemctl show testpress-worker -p CPUQuotaPerSecUSec -p MemoryMax
```

The service status showed CPU quota configured at 50%, memory maximum of 100 MB, actual memory use of approximately 4.1 MB, and peak memory of approximately 4.3 MB.

**Status:** Limits configured and verified. The worker did not exceed the memory limit, so a memory-limit-exceeded event was not demonstrated.

## 9. Automatic startup after reboot

The service was enabled:

```powershell
multipass exec testpress -- sudo systemctl enable testpress-worker
```

The VM was rebooted:

```powershell
multipass exec testpress -- sudo reboot
```

After the VM returned, its service status was checked:

```powershell
multipass exec testpress -- sudo systemctl status testpress-worker --no-pager
```

**Observed:** The VM and worker service were running after reboot.

**Status:** Tested.

## 10. Remaining topics from the broader exercise

Do not mark these as completed unless they are actually run and captured:

- `top` / `htop`: interactive process and resource monitoring.
- `pidof`: find a process ID by executable name.
- `pstree`: view parent-child process relationships.
- `jobs`, `bg`, `fg`: manage jobs started from the current shell.
- `nice`, `renice`: set or change process scheduling niceness.
- Memory-limit exhaustion: not tested; only the configured limit and normal usage were checked.
- Invalid executable and repeated-crash behaviour: not separately documented as completed.

## Screenshot evidence checklist

Save real screenshots in this folder. Suggested filenames:

1. `01-foreground-worker.png` — heartbeat and graceful Ctrl+C shutdown.
2. `02-nohup-background.png` — background worker log output.
3. `03-process-inspection.png` — `ps` and `pgrep` output.
4. `04-systemd-status.png` — active service, non-root user, and MainPID.
5. `05-graceful-sigterm.png` — journal showing SIGTERM and graceful shutdown.
6. `06-crash-restart.png` — journal showing simulated crash and restart.
7. `07-sigkill-recovery.png` — service running again after SIGKILL.
8. `08-environment-file.png` — environment file path reported by systemd.
9. `09-resource-limits.png` — CPUQuota and MemoryMax configuration/status.
10. `10-reboot-autostart.png` — service active after VM reboot.

Only include screenshots you actually capture. Do not present an uncaptured screenshot as evidence.
