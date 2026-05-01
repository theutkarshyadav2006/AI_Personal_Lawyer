from app import app
from database.models import Case, User
with app.app_context():
    client = User.query.filter_by(email='client@example.com').first()
    case = Case.query.filter_by(client_id=client.id).first()
    if case:
        print(case.id)
    else:
        print("None")
