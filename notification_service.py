"""
Notification Dispatcher Service
Co-authored feature by Emmanuel Saleem and Collaborators
"""

class AttendanceNotifier:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url

    def send_alert(self, student_name, absent_days):
        message = f"Alert: {student_name} has been absent for {absent_days} consecutive days."
        return {"status": "dispatched", "message": message}

if __name__ == '__main__':
    notifier = AttendanceNotifier()
    print(notifier.send_alert("John Doe", 3))
