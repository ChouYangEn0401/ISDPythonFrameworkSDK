.venv\Scripts\python.exe -m pytest -v tests/base/singleton_test.py

.venv\Scripts\python.exe -m pytest -v tests/events/event_test.py
.venv\Scripts\python.exe -m pytest -v tests/events/multicallbacks.py

.venv\Scripts\python.exe -m pytest -v tests/events/delay_test.py

.venv\Scripts\python.exe -m pytest -v tests/logger/file_logger.py
.venv\Scripts\python.exe -m pytest -v tests/logger/terminal_logger.py
.venv\Scripts\python.exe -m pytest -v tests/logger/tkinter_logger.py

.venv\Scripts\python.exe -m pytest -v tests/helpers/assertions_test.py
.venv\Scripts\python.exe -m pytest -v tests/helpers/decorators_test.py
.venv\Scripts\python.exe -m pytest -v tests/helpers/exceptions_test.py
