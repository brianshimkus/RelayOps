from sqlmodel import Session, select

from app.database import engine
from app.models import Tenant

TENANTS = [
    ("meridian-payments", "Meridian Payments", "payments"),
    ("northstar-brokerage", "Northstar Brokerage", "brokerage"),
    ("harbor-lending", "Harbor Lending", "lending"),
]


def main() -> None:
    with Session(engine) as db:
        for slug, name, domain in TENANTS:
            exists = db.exec(select(Tenant).where(Tenant.slug == slug)).first()
            if not exists:
                db.add(Tenant(slug=slug, name=name, domain=domain))
        db.commit()


if __name__ == "__main__":
    main()