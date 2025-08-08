from fastapi import Request
from starlette.datastructures import Headers, URL
from backend.core.database import SessionLocal
from backend.core.models import Hospital
from backend.middleware.tenant_middleware import setup_tenant_context, tenant_middleware

# Note: This script is for direct CLI testing, not FastAPI runtime

class DummyRequest:
    def __init__(self, path):
        self.url = URL(f"http://localhost{path}")
        self.headers = Headers({})

if __name__ == "__main__":
    db = SessionLocal()
    print("Testing valid slug /h/demo1 ...")
    request = DummyRequest("/h/demo1")
    try:
        setup_tenant_context(request, db)
        hid = tenant_middleware.get_hospital_context()
        print(f"✅ /h/demo1: hospital_id set to {hid}")
    except Exception as e:
        print(f"❌ /h/demo1: {e}")

    print("Testing invalid slug /h/invalidslug ...")
    request = DummyRequest("/h/invalidslug")
    try:
        setup_tenant_context(request, db)
        hid = tenant_middleware.get_hospital_context()
        print(f"❌ /h/invalidslug: should have raised 404, got hospital_id={hid}")
    except Exception as e:
        if hasattr(e, 'status_code') and getattr(e, 'status_code', None) == 404:
            print(f"✅ /h/invalidslug: correctly raised 404 Hospital not found")
        else:
            print(f"❌ /h/invalidslug: raised unexpected exception: {e}")
    db.close() 