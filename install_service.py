import sys
import os
import subprocess

def main():
    print("==========================================================")
    print("Installing ZKTeco K50 Biometric Sync Agent as Windows Service")
    print("==========================================================")
    print("[NOTE] Ensure this terminal is running as Administrator.")

    # 1. Install pywin32 if missing
    try:
        import win32serviceutil
    except ImportError:
        print("[INFO] pywin32 not found. Installing now...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
            print("[OK] pywin32 installed successfully.")
        except Exception as e:
            print(f"[FAIL] Failed to install pywin32: {str(e)}")
            sys.exit(1)

    # Make sure other core dependencies are installed system-wide
    print("[INFO] Verifying sync agent dependencies are installed system-wide...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "python-dotenv", "pyzk"])
        print("[OK] Dependencies verified.")
    except Exception as e:
        print(f"[WARNING] Failed to verify system-wide packages: {str(e)}")

    # 2. Automatically locate and run pywin32_postinstall.py to register DLLs
    post_install_paths = [
        os.path.join(sys.prefix, "Scripts", "pywin32_postinstall.py"),
        os.path.join(os.path.dirname(sys.executable), "Scripts", "pywin32_postinstall.py"),
        os.path.join(sys.prefix, "pywin32_postinstall.py"),
    ]
    
    appdata = os.getenv("APPDATA")
    if appdata:
        post_install_paths.append(os.path.join(appdata, "Python", f"Python{sys.version_info.major}{sys.version_info.minor}", "Scripts", "pywin32_postinstall.py"))

    found_script = None
    for path in post_install_paths:
        if os.path.exists(path):
            found_script = path
            break

    if found_script:
        print(f"[INFO] Running pywin32 post-installation from: {found_script}")
        try:
            subprocess.check_call([sys.executable, found_script, "-install"])
            print("[OK] pywin32 post-installation completed successfully.")
        except Exception as e:
            print(f"[WARNING] Post-installation setup script failed (likely files are in use): {str(e)}")
    else:
        print("[WARNING] Could not locate pywin32_postinstall.py. Attempting to proceed...")

    # 3. Verify modules can be imported
    try:
        import win32serviceutil
        import main_service
    except ImportError as e:
        print(f"[FAIL] Failed to import win32 modules after setup: {str(e)}")
        print("Please open a new Administrator PowerShell window and run the installer again.")
        sys.exit(1)

    # 4. Install the service
    sys.argv = [sys.argv[0], "install"]
    try:
        win32serviceutil.HandleCommandLine(main_service.BiometricSyncService)
        
        # Write PythonPath value to BOTH registry subkeys (PythonClass and Parameters)
        import winreg
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Key 1: PythonClass
            reg_path_1 = r"System\CurrentControlSet\Services\BiometricSyncAgent\PythonClass"
            key1 = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_path_1)
            winreg.SetValueEx(key1, "PythonPath", 0, winreg.REG_SZ, current_dir)
            winreg.CloseKey(key1)
            
            # Key 2: Parameters
            reg_path_2 = r"System\CurrentControlSet\Services\BiometricSyncAgent\Parameters"
            key2 = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_path_2)
            winreg.SetValueEx(key2, "PythonPath", 0, winreg.REG_SZ, current_dir)
            winreg.CloseKey(key2)

            # Key 3: Root Service Key
            reg_path_3 = r"System\CurrentControlSet\Services\BiometricSyncAgent"
            key3 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path_3, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key3, "PythonPath", 0, winreg.REG_SZ, current_dir)
            winreg.CloseKey(key3)
            
            print(f"[OK] Service PythonPath registered: {current_dir}")
        except Exception as reg_err:
            print(f"[WARNING] Could not write registry PythonPath: {str(reg_err)}")

        print("[OK] Windows Service installed successfully.")
        print("\nTo start the service, run:")
        print("  net start BiometricSyncAgent")
    except Exception as e:
        print(f"[FAIL] Failed to install service: {str(e)}")

if __name__ == '__main__':
    main()
