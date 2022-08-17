#!/bin/bash
if [ "$1" == "test" ]
then
	python -m unittest test.test_network test.test_PoW test.test_files test.test_PoS -vv
else
	python -m streamlit run app/main.py
fi
