CALL "%VENVS%\incidents34\Scripts\activate.bat"
SET FLASK_APP=incidents/__init__.py
SET FLASK_DEBUG=1
flask run
