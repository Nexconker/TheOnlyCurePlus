"""Copia el mod y las herramientas al repositorio de GitHub (TOCPlus/github/TheOnlyCurePlus).
El mod se publica tal cual está en Zomboid/mods (lo que juega la gente) y las herramientas sin salidas
pesadas (renders, escenas, .blend). Uso: python sync_repo.py"""
import os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(os.path.dirname(HERE), "github", "TheOnlyCurePlus")
MOD = os.path.join(os.path.expanduser("~"), "Zomboid", "mods", "TheOnlyCurePlus")

IGN = shutil.ignore_patterns("__pycache__", "*.pyc", "out", "*.blend", "*.blend1", "*.bak*", "Thumbs.db", ".git", "models")
os.makedirs(REPO, exist_ok=True)
for sub, src in (("TheOnlyCurePlus", MOD), ("tools", HERE)):
    dst = os.path.join(REPO, sub)
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=IGN)
n = sum(len(f) for _, _, f in os.walk(REPO) if ".git" not in _)
print("repo sincronizado:", REPO, "-", n, "archivos")
