"""
Attendance Audit Logging System
Author: Emmanuel saleem (netizen)
Co-authored-by: Emmanuel Saleem (es-77)
"""

import datetime

class AuditLogger:
    def __init__(self, log_path="attendance_audit.log"):
        self.log_path = log_path

    def log_event(self, action, user_id, details):
        timestamp = datetime.datetime.utcnow().isoformat()
        entry = f"[{timestamp}] ACTION={action} USER={user_id} DETAILS={details}\n"
        return entry

if __name__ == '__main__':
    logger = AuditLogger()
    print(logger.log_event("LOGIN", "101662490", "System audit record initialized"))
