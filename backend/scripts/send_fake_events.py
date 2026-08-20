#!/usr/bin/env python
"""
SIH1349 Demo Event Generator

Generates fake AI events for dashboard development and testing.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
import random
import time
from datetime import datetime

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)