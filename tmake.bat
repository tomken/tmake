echo off
python %~dp0\tmake.py %~dp0 %*
exit /b %errorlevel%