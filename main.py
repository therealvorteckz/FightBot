#!/usr/bin/env python
# IRC Fightbot - Friendly Chat Fightbbot

import os
import sys
import importlib
from time import sleep
import asyncio
import logging

import irc

print('#'*56)
print('#{0}#'.format(''.center(54)))
print('#{0}#'.format('FightBot'.center(54)))
print('#{0}#'.format('Developed by vorteckz in Python'.center(54)))
print('#{0}#'.format(' with help from acidvegas that MUTHAFUCK'.center(54)))
print('#{0}#'.format('https://github.com/therealvorteckz/FightBot'.center(54)))
print('#{0}#'.format(''.center(54)))
print('#'*56)


irc.run()