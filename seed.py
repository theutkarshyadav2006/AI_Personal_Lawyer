from app import app
from database.extensions import db
from database.models import User, LawyerProfile

with app.app_context():
    # Check if lawyers already exist
    if User.query.filter_by(role='lawyer').first() is None:
        print("Seeding dummy lawyers...")
        
        # Lawyer 1
        lawyer1 = User(name="Adv. Rajat Sharma", email="rajat@example.com", role="lawyer")
        lawyer1.set_password("password123")
        db.session.add(lawyer1)
        db.session.commit()
        
        profile1 = LawyerProfile(
            user_id=lawyer1.id,
            specialization="Property Law, Real Estate",
            experience_years=15,
            rating=4.9,
            bio="Specializes in Property Law, Real Estate Disputes, and Contract Verifications."
        )
        db.session.add(profile1)
        
        # Lawyer 2
        lawyer2 = User(name="Adv. Priya Patel", email="priya@example.com", role="lawyer")
        lawyer2.set_password("password123")
        db.session.add(lawyer2)
        db.session.commit()
        
        profile2 = LawyerProfile(
            user_id=lawyer2.id,
            specialization="Family Law, Divorce",
            experience_years=10,
            rating=4.7,
            bio="Expert in Family Law, Divorce, and Child Custody. Compassionate approach with strong courtroom presence."
        )
        db.session.add(profile2)
        
        # Lawyer 3
        lawyer3 = User(name="Adv. Vikram Singh", email="vikram@example.com", role="lawyer")
        lawyer3.set_password("password123")
        db.session.add(lawyer3)
        db.session.commit()
        
        profile3 = LawyerProfile(
            user_id=lawyer3.id,
            specialization="Criminal Defense",
            experience_years=20,
            rating=4.8,
            bio="Criminal Defense Attorney. Handles bail proceedings, cybercrimes, and white-collar fraud."
        )
        db.session.add(profile3)
        
        db.session.commit()
        print("Seeded successfully!")
    else:
        print("Lawyers already exist. Skipping seed.")
