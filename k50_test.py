from zk import ZK
from datetime import datetime

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370

def main():
    zk = ZK(
        DEVICE_IP,
        port=DEVICE_PORT,
        timeout=10,
        password=0,
        force_udp=False,
        ommit_ping=False,
    )

    conn = None

    try:
        print(f"Connecting to K50 at {DEVICE_IP}:{DEVICE_PORT}...")

        conn = zk.connect()

        print("SUCCESS: Connected to K50")
        print("-" * 60)

        # Device information
        print("Device:", conn.get_device_name())
        print("Serial:", conn.get_serialnumber())
        print("Firmware:", conn.get_firmware_version())
        print("Platform:", conn.get_platform())

        print("-" * 60)

        # Read attendance records
        print("Reading attendance records...")

        attendance = conn.get_attendance()

        print(f"Total records: {len(attendance)}")
        print("-" * 60)

        for record in attendance:
            print(
                f"User ID: {record.user_id} | "
                f"Time: {record.timestamp} | "
                f"Status: {record.status} | "
                f"Punch: {record.punch}"
            )

        print("-" * 60)
        print("Done.")

    except Exception as e:
        print("ERROR:")
        print(type(e).__name__, str(e))

    finally:
        if conn:
            try:
                conn.disconnect()
                print("Disconnected from K50")
            except Exception:
                pass


if __name__ == "__main__":
    main()