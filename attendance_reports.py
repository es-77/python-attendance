"""
Automated Attendance Analytics and Reporting Module
Collaborative feature by Emmanuel Saleem and Team
"""

class AttendanceAnalytics:
    def __init__(self, records):
        self.records = records

    def calculate_attendance_rate(self):
        if not self.records:
            return 0.0
        present = sum(1 for r in self.records if r.get('status') == 'present')
        return round((present / len(self.records)) * 100, 2)

    def generate_summary(self):
        return {
            'total_students': len(self.records),
            'attendance_rate': self.calculate_attendance_rate()
        }

if __name__ == '__main__':
    sample = [{'name': 'Alice', 'status': 'present'}, {'name': 'Bob', 'status': 'present'}]
    analytics = AttendanceAnalytics(sample)
    print("Report Summary:", analytics.generate_summary())
