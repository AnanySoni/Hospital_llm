from backend.core.database import SessionLocal
from backend.core.models import Hospital, Doctor, User, TestResult, AdminUser

def main():
    db = SessionLocal()
    print('--- Data Integrity Check ---')
    # 1. Hospitals: unique, non-null slug
    hospitals = db.query(Hospital).all()
    slugs = set()
    issues = False
    for h in hospitals:
        if not getattr(h, 'slug', None):
            print(f'❌ Hospital id={h.id} name={h.name} has missing slug')
            issues = True
        elif h.slug in slugs:
            print(f'❌ Duplicate slug found: {h.slug}')
            issues = True
        else:
            slugs.add(h.slug)
    # 2. Doctors and Users: valid hospital_id
    for d in db.query(Doctor).all():
        if d.hospital_id is None:
            print(f'❌ Doctor id={d.id} name={d.name} missing hospital_id')
            issues = True
    for u in db.query(User).all():
        if u.hospital_id is None:
            print(f'❌ User id={u.id} name={u.name} missing hospital_id')
            issues = True
    # 3. Tests: hospital_id should be NULL (global)
    for t in db.query(TestResult).all():
        if t.hospital_id is not None:
            print(f'❌ TestResult id={t.id} should be global (hospital_id=NULL), found hospital_id={t.hospital_id}')
            issues = True
    # 4. Admin users: super admin is global, hospital admins have valid hospital_id
    for a in db.query(AdminUser).all():
        if getattr(a, 'is_super_admin', False):
            if a.hospital_id is not None:
                print(f'❌ Super admin id={a.id} should not be tied to a hospital (hospital_id={a.hospital_id})')
                issues = True
        else:
            if a.hospital_id is None:
                print(f'❌ Hospital admin id={a.id} username={a.username} missing hospital_id')
                issues = True
    if not issues:
        print('✅ Data integrity check passed!')
    db.close()

if __name__ == "__main__":
    main() 