"""API + dashboard sederhana (Flask, pure-Python agar aman di s390x).
Jalankan:  python -m trailguard.api.app   -> http://localhost:8000
"""
import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from ..config import load_config, path_of
from ..models.score import score_frame
from ..models.train import load_bundle
from ..policy.policy import decide, policy_cfg