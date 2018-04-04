#!/bin/bash

ps -eaf | grep 'python server/fmserver.py' | grep -v grep | awk '{print $2}' | xargs kill

