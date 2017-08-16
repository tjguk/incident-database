import os, sys

from incidents import db, IncidentStatus

if __name__ == '__main__':
    if os.path.exists("incidents/incidents.db"):
        os.remove("incidents/incidents.db")

    db.create_all()

    db.session.add(IncidentStatus("Open", 1))
    db.session.add(IncidentStatus("Pending", 2))
    db.session.add(IncidentStatus("Closed", 3))

    db.session.commit()
