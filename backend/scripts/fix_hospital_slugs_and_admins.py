from backend.core.database import SessionLocal
from backend.core.models import Hospital, AdminUser

def main():
    db = SessionLocal()
    # Update hospital slugs
    hospital_updates = {
        1: 'demo1',
        2: 'apollo',
    }
    for hospital_id, slug in hospital_updates.items():
        hospital = db.query(Hospital).filter_by(id=hospital_id).first()
        if hospital is not None:
            print(f'Updating hospital id={hospital_id} to slug={slug}')
            setattr(hospital, 'slug', slug)
    db.commit()
    # Update admin usernames/emails
    for admin in db.query(AdminUser).all():
        if getattr(admin, 'is_super_admin', None) is False:
            hospital = db.query(Hospital).filter_by(id=admin.hospital_id).first()
            if hospital is not None and getattr(hospital, 'slug', None):
                new_username = f'admin_{hospital.slug}'
                new_email = f'{new_username}@{hospital.slug}.com'
                print(f'Updating admin id={admin.id} to username={new_username}, email={new_email}')
                setattr(admin, 'username', new_username)
                setattr(admin, 'email', new_email)
    db.commit()
    db.close()
    print('Hospital slugs and admin usernames/emails updated.')

if __name__ == "__main__":
    main() 