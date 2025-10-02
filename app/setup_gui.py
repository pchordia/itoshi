"""
Setup script for creating a standalone Mac .app bundle
Usage: python setup_gui.py py2app

Note: For now, it's easier to just distribute the source code and use ./launch_gui.sh
Building a full .app bundle is complex due to many dependencies.
"""

from setuptools import setup

APP = ['src/gui_app.py']
DATA_FILES = []  # Don't include .env - users should set up their own keys

# Simplified options - exclude heavy dependencies that cause issues
OPTIONS = {
    'argv_emulation': True,
    'packages': ['tkinter'],
    'includes': [
        'openai',
        'dotenv', 
        'PIL',
        'requests',
        'jwt'
    ],
    'excludes': [
        'numpy',
        'scipy', 
        'pandas',
        'matplotlib',
        'jax',
        'jaxlib',
        'google.generativeai',  # Exclude problematic google package
        'test',
        'tests',
        'unittest'
    ],
    'plist': {
        'CFBundleName': 'Anime Video Generator',
        'CFBundleDisplayName': 'Anime Video Generator',
        'CFBundleIdentifier': 'com.itoshi.animevideo',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    name='AnimeVideoGenerator',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

