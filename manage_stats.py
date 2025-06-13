from app.utils.stats_manager import StatsManager
from app.models import StreamingHistory
from app.database import db_session
from sqlalchemy import distinct

def calculate_stats_for_user(username):
    """Calculate stats for a specific user."""
    print(f"[INFO] Calculating stats for user: {username}")

    try:
        stats = StatsManager.calculate_stats_for_user(username)
        print(f"[SUCCESS] Stats calculated for '{username}'")
        print(f"  - Calculated at: {stats['calculated_at']}")
        print(f"  - Unique tracks: {stats['unique_tracks_count']['unique_tracks_count']}")
        print(f"  - Total listening time: {stats['total_listening_time']['total_listening_hours']:.2f} hours")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to calculate stats for '{username}': {e}")
        return False


def calculate_stats_for_all_users():
    """Calculate stats for all users who have listening history."""
    print("[INFO] Fetching users with listening history...")

    users = db_session.query(distinct(StreamingHistory.username)).all()
    users = [user[0] for user in users if user[0]]

    if not users:
        print("[WARN] No users found with listening history.")
        return

    print(f"[INFO] Found {len(users)} user(s): {', '.join(users)}")

    success_count = 0
    for username in users:
        if calculate_stats_for_user(username):
            success_count += 1
        print("-" * 40)

    print(f"[SUMMARY] Stats calculated for {success_count}/{len(users)} users.")


def check_stats_status(username):
    """Check stats status for a user."""
    exists = StatsManager.stats_exist_for_user(username)
    calculation_date = StatsManager.get_stats_calculation_date(username)

    print(f"[INFO] Stats status for user '{username}':")
    print(f"  - Exists: {'Yes' if exists else 'No'}")
    print(f"  - Last calculated: {calculation_date if calculation_date else 'Never'}")


def list_all_users():
    """List all users with listening history."""
    users = db_session.query(distinct(StreamingHistory.username)).all()
    users = [user[0] for user in users if user[0]]

    if not users:
        print("[INFO] No users with listening history found.")
        return

    print(f"[INFO] Users with listening history ({len(users)}):")
    for username in users:
        exists = StatsManager.stats_exist_for_user(username)
        calculation_date = StatsManager.get_stats_calculation_date(username)
        date_str = calculation_date.strftime("%Y-%m-%d %H:%M") if calculation_date else "Never"
        print(f"  - {username.ljust(20)} | Stats: {'Yes' if exists else 'No'} | Last calculated: {date_str}")



if __name__ == "__main__":
    calculate_stats_for_all_users()
    # calculate_stats_for_user('dionisiy')
    # check_stats_status('dionisiy')
    # list_all_users()