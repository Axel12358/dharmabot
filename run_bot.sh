#!/bin/bash
cd "$(dirname "$0")"
.venv/bin/python main.py >> bot.log 2>&1
echo "Bot started at $(date)"
