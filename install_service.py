import sys
import os
import subprocess

def main():
    print("==========================================================")
    print("Installing ZKTeco K50 Biometric Sync Agent as Windows Service")
    print("==========================================================")
    print("[NOTE] Ensure this terminal is running as Administrator.")

    # Check for pywin32 installation
    try:
        import win32serviceutil
    except ImportError:
        print("[INFO] pywin32 not found. Installing now...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
            print("[OK] pywin32 installed successfully.")
        except Exception as e:
            print(f"[FAIL] Failed to install pywin32: {str(e)}")
            print("Please run: pip install pywin32 manually in Administrator command prompt.")
            sys.exit(1)

    import win32serviceutil
    import main_service

    # Append command line args
    sys.argv = [sys.argv[0], "install"]
    try:
        win32serviceutil.HandleCommandLine(main_service.BiometricSyncService)
        print("[OK] Windows Service installed successfully.")
        print("You can start it by running: net start BiometricSyncAgent")
    except Exception as e:
        print(f"[FAIL] Failed to install service: {str(e)}")

if __name__ == '__main__':
    main()
