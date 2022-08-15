@echo off
cls
if "%1" == "test" (python -m unittest test.test_network -vv) else (python -m streamlit run app\main.py --logger.level=critical)