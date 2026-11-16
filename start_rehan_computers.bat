@echo off
title Rehan Computers - Hardware Storefront & System
echo ==============================================================
echo   REHAN LAPTOP & COMPUTER - SARGODHA
echo   Shop #96, 1st Floor, Trust Plaza, Sargodha
echo   Helpline: 0300-9607829
echo ==============================================================

echo Launching Rehan Computers Storefront in your browser...
start "" "http://127.0.0.1:8000/"

echo Starting Backend Engine on http://127.0.0.1:8000...
python run_server.py
pause
