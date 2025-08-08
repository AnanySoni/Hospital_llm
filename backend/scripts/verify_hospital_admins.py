from backend.core.database import SessionLocal
from backend.core.models import Hospital, AdminUser

def main():
    db = SessionLocal()
    print('--- Hospitals ---')
    for h in db.query(Hospital).all():
        print(f'id={h.id}, slug={getattr(h, "slug", None)}, name={h.name}')
    print('--- Admin Users ---')
    for a in db.query(AdminUser).all():
        print(f'id={a.id}, username={a.username}, hospital_id={a.hospital_id}, is_super_admin={a.is_super_admin}')
    db.close()

if __name__ == "__main__":
    main() 