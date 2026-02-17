#!/usr/bin/env python3
"""
Standalone script to run the Fire Vision Pro background service
This allows cameras and streaming to continue running even when the GUI is closed
"""

import sys
import os
import argparse
import signal
import time
from background_service import BackgroundService

def main():
    parser = argparse.ArgumentParser(description='Fire Vision Pro Background Service')
    parser.add_argument('--config-dir', default='config', help='Configuration directory')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--stop', action='store_true', help='Stop running service')
    parser.add_argument('--status', action='store_true', help='Show service status')
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
        return
    
    if args.stop:
        stop_service()
        return
    
    # Start the service
    print("🚀 Starting Fire Vision Pro Background Service...")
    print("📁 Configuration directory:", args.config_dir)
    
    service = BackgroundService()
    
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down...")
        service.stop()
        sys.exit(0)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        service.start()
        
        print("✅ Background service started successfully")
        print("📊 Service status:")
        status = service.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print("\n🔄 Service running... Press Ctrl+C to stop")
        
        # Keep running
        while service.is_running():
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
    except Exception as e:
        print(f"❌ Service error: {e}")
    finally:
        service.stop()
        print("🔚 Background service stopped")

def show_status():
    """Show service status"""
    try:
        service = BackgroundService()
        status = service.get_status()
        
        print("📊 Fire Vision Pro Service Status:")
        print("=" * 40)
        for key, value in status.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"❌ Error getting status: {e}")

def stop_service():
    """Stop running service"""
    print("🛑 Stopping Fire Vision Pro Background Service...")
    # Implementation would depend on how you want to handle service management
    # This could involve PID files, system service management, etc.
    print("⚠️ Service stop functionality not implemented yet")

if __name__ == "__main__":
    main()
