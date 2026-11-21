"""Arranque:  python -m api [--puerto 8000]  →  http://localhost:8000"""
import argparse

import uvicorn

p = argparse.ArgumentParser(prog="python -m api")
p.add_argument("--puerto", type=int, default=8000)
p.add_argument("--host", default="127.0.0.1")
a = p.parse_args()
uvicorn.run("api.servidor:app", host=a.host, port=a.puerto)
