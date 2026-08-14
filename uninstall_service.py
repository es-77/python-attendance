import sys
import os

def main():
    print("==========================================================")
    print("Uninstalling ZKTeco K50 Biometric Sync Agent Service")
    print("==========================================================")
    print("[NOTE] Ensure this terminal is running as Administrator.")

    try:
        import win32serviceutil
    except ImportError:
        print("[FAIL] pywin32 is not installed. Nothing to uninstall.")
        sys.exit(1)

    import main_service

    sys.argv = [sys.argv[0], "remove"]
    try:
        win32serviceutil.HandleCommandLine(main_service.BiometricSyncService)
        print("[OK] Windows Service removed successfully.")
    except Exception as e:
        print(f"[FAIL] Failed to remove service: {str(e)}")

if __name__ == '__main__':
    main()
