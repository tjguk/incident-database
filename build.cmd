CALL "%VENVS%\incidents34\Scripts\activate.bat"
pyinstaller run.py --name incidents --exclude-module=tkinter --add-data=templates\*.html;templates
