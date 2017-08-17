#!/bin/bash

ps -eaf | grep 'python server/fmserver.py' | awk '{print $2}' | xargs kill

