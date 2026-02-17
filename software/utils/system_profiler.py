import os
import sys
import platform
import ctypes
import time
import shutil
import tempfile
import threading

import psutil

class SystemProfiler:
    """Helper class to detect system hardware and capabilities"""
    
    def __init__(self):
        self.specs = {
            'ram_gb': 0,
            'cpu_cores': 0,
            'has_gpu': False,
            'disk_speed_mbps': 0,
            'os': platform.system()
        }
        self.is_low_end = False
        
    def profile_system(self):
        """Run all checks and determine if system is low-end"""
        print("🔍 Profiling system hardware...")
        self.specs['ram_gb'] = self.get_ram_info()
        self.specs['cpu_cores'] = self.get_cpu_info()
        self.specs['has_gpu'] = self.check_gpu()
        self.specs['disk_speed_mbps'] = self.measure_disk_speed()
        
        self.is_low_end = self._evaluate_low_end(self.specs)
        
        print(f"📊 System Specs: RAM={self.specs['ram_gb']}GB, "
              f"Cores={self.specs['cpu_cores']}, "
              f"GPU={self.specs['has_gpu']}, "
              f"Disk={self.specs['disk_speed_mbps']} MB/s")
        print(f"🤖 Device Classification: {'LOW-END (NVR Mode)' if self.is_low_end else 'HIGH-PERFORMANCE'}")
        
        return self.is_low_end, self.specs

    def get_realtime_stats(self):
        """Fetch real-time system metrics (CPU, RAM, GPU, Disk)"""
        stats = {
            'cpu': {},
            'ram': {},
            'gpu': {},
            'disk': {}
        }
        
        try:
            # CPU
            stats['cpu']['usage_percent'] = psutil.cpu_percent(interval=None)
            stats['cpu']['count'] = psutil.cpu_count(logical=True)
            stats['cpu']['model'] = platform.processor()
            
            # RAM
            mem = psutil.virtual_memory()
            stats['ram']['total_gb'] = round(mem.total / (1024**3), 1)
            stats['ram']['available_gb'] = round(mem.available / (1024**3), 1)
            stats['ram']['usage_percent'] = mem.percent
            
            # Disk
            disk = psutil.disk_usage('/')
            stats['disk']['total_gb'] = round(disk.total / (1024**3), 1)
            stats['disk']['free_gb'] = round(disk.free / (1024**3), 1)
            stats['disk']['usage_percent'] = disk.percent
            
            # Disk IO (Optional, instantaneous read/write)
            try:
                io = psutil.disk_io_counters()
                # We can't easily get instantaneous speed without keeping state, 
                # but we can return the raw counters or skip for now.
                # Let's just return basic availability.
                pass 
            except:
                pass

            # GPU (via Torch if available)
            stats['gpu']['available'] = False
            try:
                import torch
                if torch.cuda.is_available():
                    stats['gpu']['available'] = True
                    stats['gpu']['model'] = torch.cuda.get_device_name(0)
                    stats['gpu']['count'] = torch.cuda.device_count()
                    # VRAM (approximate via torch or pynvml if installed, keep it simple)
                    # Torch doesn't give simple "usage %" easily without pynvml.
                    # We will mark it as available.
                    props = torch.cuda.get_device_properties(0)
                    stats['gpu']['vram_total_gb'] = round(props.total_memory / (1024**3), 1)
            except ImportError:
                pass
            except Exception as e:
                # modifying stats in case of error is fine, key existence checks in UI recommended
                pass

        except Exception as e:
            print(f"⚠️ Error fetching realtime stats: {e}")
            
        return stats

    def get_ram_info(self):
        """Get total RAM in GB using ctypes for Windows"""
        try:
            if platform.system() == "Windows":
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                return round(stat.ullTotalPhys / (1024 ** 3), 1)
            else:
                # Fallback for generic/linux (basic check)
                try:
                    return round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**3), 1)
                except:
                    return 8.0 # Optimistic fallback
        except Exception as e:
            print(f"⚠️ Error getting RAM info: {e}")
            return 4.0 # Default fallback assumption

    def get_cpu_info(self):
        """Get number of CPU cores"""
        try:
            return os.cpu_count() or 2
        except:
            return 2

    def check_gpu(self):
        """Check for dedicated GPU availability"""
        # 1. Try PyTorch if available
        try:
            import torch
            if torch.cuda.is_available():
                return True
        except ImportError:
            pass
            
        # 2. Try simple heuristic via ctypes/Windows
        # (This is tricky without external libs, so we rely mainly on PyTorch or assume no unless strong evidence)
        return False

    def measure_disk_speed(self):
        """Measure write speed with a small temporary file"""
        try:
            filename = os.path.join(tempfile.gettempdir(), "speed_test.tmp")
            data = os.urandom(50 * 1024 * 1024) # 50 MB
            
            start = time.time()
            with open(filename, "wb") as f:
                f.write(data)
            # Force write to disk
            if hasattr(os, 'fsync'):
                fd = os.open(filename, os.O_RDWR)
                os.fsync(fd)
                os.close(fd)
            end = time.time()
            
            if os.path.exists(filename):
                os.remove(filename)
                
            duration = end - start
            if duration <= 0: return 9999
            
            mb_per_sec = 50 / duration
            return int(mb_per_sec)
        except Exception as e:
            print(f"⚠️ Disk speed test failed: {e}")
            # Ensure cleanup if possible
            try:
                if os.path.exists(filename): os.remove(filename)
            except: pass
            return 100 # Default to decent speed

    def _evaluate_low_end(self, specs):
        """Determine if device is low end based on specs"""
        # Criteria for Low End:
        # RAM < 6.0GB (Allow 8GB systems with reserved memory)
        # OR
        # CPU Cores < 4 (Dual core or less)
        
        is_low_ram = specs['ram_gb'] < 6.0
        is_low_cpu = specs['cpu_cores'] < 4
        # Disk speed alone shouldn't force NVR mode if RAM/CPU are okay
        
        if is_low_ram or is_low_cpu:
            return True
            
        return False

# Global instance
profiler = SystemProfiler()
