"""
Process inspector module for reading comprehensive system metrics from /proc.
"""

import os
import pwd
import time
from typing import Dict, List, Optional, Tuple
from window_getter.core.models import ProcessInfo


# Keep track of previous /proc/<pid>/stat ticks to compute CPU %
_prev_proc_ticks: Dict[int, Tuple[float, float]] = {}


def get_cmdline(pid: int) -> List[str]:
    """Retrieve process command line list from /proc/<pid>/cmdline."""
    cmdline_path = f"/proc/{pid}/cmdline"
    if not os.path.exists(cmdline_path):
        return []
    try:
        with open(cmdline_path, "rb") as f:
            raw = f.read()
        if not raw:
            return []
        parts = [p.decode("utf-8", errors="ignore") for p in raw.split(b"\x00") if p]
        return parts
    except Exception:
        return []


def get_exe_path(pid: int) -> str:
    """Retrieve executable path from /proc/<pid>/exe symlink."""
    try:
        return os.readlink(f"/proc/{pid}/exe")
    except Exception:
        return ""


def get_cwd(pid: int) -> str:
    """Retrieve current working directory from /proc/<pid>/cwd symlink."""
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except Exception:
        return ""


def get_process_user(uid: int) -> str:
    """Convert UID to username."""
    try:
        return pwd.getpwuid(uid).pw_name
    except Exception:
        return str(uid)


def get_parent_name(ppid: int) -> str:
    """Retrieve process name for parent PID."""
    if ppid <= 0:
        return ""
    status_file = f"/proc/{ppid}/status"
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("Name:"):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
    return ""


def get_environ(pid: int) -> Dict[str, str]:
    """Retrieve process environment variables from /proc/<pid>/environ."""
    env_file = f"/proc/{pid}/environ"
    if not os.path.exists(env_file):
        return {}
    try:
        with open(env_file, "rb") as f:
            raw = f.read()
        if not raw:
            return {}
        result = {}
        entries = raw.split(b"\x00")
        for entry in entries:
            if not entry:
                continue
            decoded = entry.decode("utf-8", errors="ignore")
            if "=" in decoded:
                k, v = decoded.split("=", 1)
                result[k] = v
        return result
    except Exception:
        return {}


def get_fd_details(pid: int, limit: int = 30) -> List[str]:
    """Retrieve detailed open file descriptors symlinks from /proc/<pid>/fd."""
    fd_dir = f"/proc/{pid}/fd"
    if not os.path.exists(fd_dir):
        return []
    result = []
    try:
        entries = os.listdir(fd_dir)
        # Sort numerically
        sorted_entries = sorted(entries, key=lambda x: int(x) if x.isdigit() else 999999)
        for entry in sorted_entries[:limit]:
            fd_path = os.path.join(fd_dir, entry)
            try:
                target = os.readlink(fd_path)
                result.append(f"fd {entry} -> {target}")
            except Exception:
                result.append(f"fd {entry}")
    except Exception:
        pass
    return result


def get_io_stats(pid: int) -> Tuple[float, float]:
    """Retrieve read and write bytes in MB from /proc/<pid>/io."""
    io_file = f"/proc/{pid}/io"
    if not os.path.exists(io_file):
        return (0.0, 0.0)
    read_bytes = 0
    write_bytes = 0
    try:
        with open(io_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("read_bytes:"):
                    read_bytes = int(line.split(":", 1)[1].strip())
                elif line.startswith("write_bytes:"):
                    write_bytes = int(line.split(":", 1)[1].strip())
        return (round(read_bytes / (1024.0 * 1024.0), 2), round(write_bytes / (1024.0 * 1024.0), 2))
    except Exception:
        return (0.0, 0.0)


def get_start_time_and_uptime(pid: int) -> Tuple[str, str]:
    """Calculate process start time and running uptime from /proc/<pid>/stat and /proc/uptime."""
    stat_file = f"/proc/{pid}/stat"
    uptime_file = "/proc/uptime"
    if not os.path.exists(stat_file) or not os.path.exists(uptime_file):
        return ("", "")

    try:
        with open(uptime_file, "r") as f:
            sys_uptime = float(f.read().split()[0])

        with open(stat_file, "r") as f:
            data = f.read().split()

        # field 21 (0-indexed) is starttime in jiffies after system boot
        starttime_jiffies = float(data[21])
        clock_ticks = os.sysconf("SC_CLK_TCPS") if hasattr(os, "sysconf") else 100
        proc_start_sec_after_boot = starttime_jiffies / clock_ticks

        proc_uptime_sec = sys_uptime - proc_start_sec_after_boot
        if proc_uptime_sec < 0:
            proc_uptime_sec = 0.0

        # Formatted uptime
        hrs = int(proc_uptime_sec // 3600)
        mins = int((proc_uptime_sec % 3600) // 60)
        secs = int(proc_uptime_sec % 60)

        if hrs > 0:
            uptime_str = f"{hrs}h {mins}m {secs}s"
        elif mins > 0:
            uptime_str = f"{mins}m {secs}s"
        else:
            uptime_str = f"{secs}s"

        start_timestamp = time.time() - proc_uptime_sec
        start_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_timestamp))

        return (start_time_str, uptime_str)
    except Exception:
        return ("", "")


def get_process_info(pid: int) -> ProcessInfo:
    """
    Fetch comprehensive process stats from /proc/<pid>.
    """
    proc_dir = f"/proc/{pid}"
    if not os.path.exists(proc_dir):
        return ProcessInfo(pid=pid, status="dead")

    name = ""
    ppid = 0
    status = "running"
    threads = 1
    uid = 0
    memory_mb = 0.0
    vm_size_mb = 0.0
    vm_peak_mb = 0.0
    vm_swap_mb = 0.0
    voluntary_ctxt = 0
    nonvoluntary_ctxt = 0

    # Parse /proc/<pid>/status
    status_file = os.path.join(proc_dir, "status")
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("Name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("PPid:"):
                        ppid = int(line.split(":", 1)[1].strip())
                    elif line.startswith("State:"):
                        status = line.split(":", 1)[1].strip()
                    elif line.startswith("Threads:"):
                        threads = int(line.split(":", 1)[1].strip())
                    elif line.startswith("Uid:"):
                        uid_str = line.split(":", 1)[1].strip().split()[0]
                        uid = int(uid_str)
                    elif line.startswith("VmRSS:"):
                        rss_kb = int(line.split(":", 1)[1].strip().split()[0])
                        memory_mb = round(rss_kb / 1024.0, 2)
                    elif line.startswith("VmSize:"):
                        vmsz_kb = int(line.split(":", 1)[1].strip().split()[0])
                        vm_size_mb = round(vmsz_kb / 1024.0, 2)
                    elif line.startswith("VmPeak:"):
                        vmpk_kb = int(line.split(":", 1)[1].strip().split()[0])
                        vm_peak_mb = round(vmpk_kb / 1024.0, 2)
                    elif line.startswith("VmSwap:"):
                        vmsw_kb = int(line.split(":", 1)[1].strip().split()[0])
                        vm_swap_mb = round(vmsw_kb / 1024.0, 2)
                    elif line.startswith("voluntary_ctxt_switches:"):
                        voluntary_ctxt = int(line.split(":", 1)[1].strip())
                    elif line.startswith("nonvoluntary_ctxt_switches:"):
                        nonvoluntary_ctxt = int(line.split(":", 1)[1].strip())
        except Exception:
            pass

    user = get_process_user(uid)
    parent_name = get_parent_name(ppid)
    cmdline = get_cmdline(pid)
    exe_path = get_exe_path(pid)
    cwd = get_cwd(pid)
    environ = get_environ(pid)
    fd_details = get_fd_details(pid, limit=30)
    open_fds = len(fd_details)
    read_mb, write_mb = get_io_stats(pid)
    start_time_str, uptime_str = get_start_time_and_uptime(pid)

    # Calculate CPU % sample delta
    cpu_percent = _calculate_cpu_percent(pid)

    return ProcessInfo(
        pid=pid,
        name=name,
        ppid=ppid,
        parent_name=parent_name,
        exe_path=exe_path,
        cwd=cwd,
        cmdline=cmdline,
        memory_mb=memory_mb,
        vm_size_mb=vm_size_mb,
        vm_peak_mb=vm_peak_mb,
        vm_swap_mb=vm_swap_mb,
        cpu_percent=cpu_percent,
        threads=threads,
        user=user,
        status=status,
        open_fds=open_fds,
        start_time_str=start_time_str,
        uptime_str=uptime_str,
        read_bytes_mb=read_mb,
        write_bytes_mb=write_mb,
        voluntary_ctxt_switches=voluntary_ctxt,
        nonvoluntary_ctxt_switches=nonvoluntary_ctxt,
        environ=environ,
        fd_details=fd_details
    )


def _calculate_cpu_percent(pid: int) -> float:
    """Calculate CPU usage percentage using /proc/<pid>/stat and total system ticks."""
    global _prev_proc_ticks
    stat_file = f"/proc/{pid}/stat"
    if not os.path.exists(stat_file):
        return 0.0

    try:
        with open(stat_file, "r") as f:
            data = f.read().split()
        # utime (index 13) + stime (index 14)
        utime = float(data[13])
        stime = float(data[14])
        total_ticks = utime + stime
        now = time.time()

        if pid in _prev_proc_ticks:
            prev_ticks, prev_time = _prev_proc_ticks[pid]
            time_delta = now - prev_time
            if time_delta > 0:
                ticks_delta = total_ticks - prev_ticks
                clock_ticks_per_sec = os.sysconf("SC_CLK_TCPS") if hasattr(os, "sysconf") else 100
                cpu_usage = (ticks_delta / clock_ticks_per_sec) / time_delta * 100.0
                _prev_proc_ticks[pid] = (total_ticks, now)
                return round(cpu_usage, 1)

        _prev_proc_ticks[pid] = (total_ticks, now)
        return 0.0
    except Exception:
        return 0.0
