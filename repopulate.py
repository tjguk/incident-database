import os, sys

from incidents import db, Pupil, Incident, IncidentStatus, Attachment

if __name__ == '__main__':
    if os.path.exists("incidents/incidents.db"):
        os.remove("incidents/incidents.db")

    db.create_all()

    db.session.add(IncidentStatus("Open", 1))
    db.session.add(IncidentStatus("Pending", 2))
    db.session.add(IncidentStatus("Closed", 3))

    db.session.add(Pupil("Tim Golden"))
    db.session.add(Pupil("Chris Doran"))
    db.session.add(Pupil("Stephen Davis"))
    db.session.add(Pupil("Pedro Virgili"))
    db.session.add(Pupil("Charlie Strinati"))
    db.session.add(Pupil("Pablo Hinojo"))

    i1 = Incident("An incident occurred", "This is the description of the incident")
    tim = Pupil.query.filter_by(name="Tim Golden").first()
    stephen = Pupil.query.filter_by(name="Stephen Davis").first()
    i1.pupils = [tim, stephen]
    i1.is_racial = 1
    i1.other_type = "Blancmange"
    db.session.add(i1)

    i2 = Incident("A second incident occurred", "This is the description of the second incident")
    i2.status = "Closed"
    chris = Pupil.query.filter_by(name="Chris Doran").first()
    i2.pupils = [chris]
    i2.attachments = [Attachment("misc/example.pdf")]
    i2.is_bullying = 1
    db.session.add(i2)

    db.session.commit()
