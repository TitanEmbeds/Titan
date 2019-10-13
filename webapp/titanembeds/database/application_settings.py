from titanembeds.database import db

class ApplicationSettings(db.Model):
    __tablename__ = "application_settings"
    id = db.Column(db.Integer, primary_key=True, nullable=False)                        # Auto increment id
    donation_goal_progress = db.Column(db.Integer, nullable=False, server_default="0")  # Current progress towards donation goal
    donation_goal_total = db.Column(db.Integer, nullable=False, server_default="0")     # Total donation required to hit goal. 0 to now show banners
    donation_goal_end = db.Column(db.Date(), nullable=True)                         # When to end donation goal

    def __init__(self):
        self.donation_goal_progress = 0
        self.donation_goal_total = 0
        self.donation_goal_end = None
