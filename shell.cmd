CALL "%VENVS%\incidents\Scripts\activate.bat"
python -i -c "from incidents import db, Pupil, Incident, Attachment"
