from titanembeds.database import db

class UserCSS(db.Model):
    __tablename__ = "user_css"
    id = db.Column(db.Integer, primary_key=True)                    # Auto increment id
    name = db.Column(db.String(255), nullable=False)                # CSS Name
    user_id = db.Column(db.String(255), nullable=False)             # Discord client ID of the owner of the css (can edit)
    css = db.Column(db.Text(4294967295))                            # CSS contents

    def __init__(self, name, user_id, css=None):
        self.name = name
        self.user_id = user_id
        self.css = css
