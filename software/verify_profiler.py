import sys
import os

# Adjust path to find utils
sys.path.append(os.path.abspath("d:/giit/FIrevision_demo/python_client"))

try:
    from utils.system_profiler import profiler
    print("Testing get_realtime_stats()...")
    stats = profiler.get_realtime_stats()
    print("Result:", stats)
    
    # Assertions
    assert 'cpu' in stats, "Missing CPU stats"
    assert 'usage_percent' in stats['cpu'], "Missing CPU usage"
    
    assert 'ram' in stats, "Missing RAM stats"
    assert 'total_gb' in stats['ram'], "Missing RAM total"
    
    assert 'gpu' in stats, "Missing GPU stats"
    
    assert 'disk' in stats, "Missing Disk stats"
    assert 'free_gb' in stats['disk'], "Missing Disk free space"
    
    print("\n✅ Verification Successful: get_realtime_stats() is working!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
except AssertionError as e:
    print(f"❌ Assertion Error: {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
