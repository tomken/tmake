echo off
python -B %~dp0\tmake.py %~dp0 %*
exit /b %errorlevel%