from datetime import datetime, timedelta
from app import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
try:
    from meta import DEBUG
    print('DEBUG', DEBUG)

except:
    DEBUG = False



class BBWP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    ticker =  db.Column(db.String, unique=False, nullable=False)
    timeframe =  db.Column(db.String, unique=False, nullable=False)
    ema =  db.Column(db.String, unique=False, nullable=False)
    value =  db.Column(db.String, unique=False, nullable=False)
    info =  db.Column(db.String, unique=False, nullable=False)
    extra =  db.Column(db.String, unique=False, nullable=False)


class MyModelView(ModelView):
    def is_accessible(self):
        return DEBUG


admin = Admin(app)

admin.add_view(MyModelView(BBWP, db.session))

