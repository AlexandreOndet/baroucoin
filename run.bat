@echo off
cls
if "%1" == "test" (python -m unittest test.test_network -vv) else (python -m app.main)