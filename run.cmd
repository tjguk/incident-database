CALL "%VENVS%\incidents\Scripts\activate.bat"
SET FLASK_APP=incidents/__init__.py
SET FLASK_DEBUG=1
flask run
