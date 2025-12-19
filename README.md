# Sea Life Gacha Game

A Flask-based web application that allows users to collect marine creatures through a gacha (random pull) system using an in-game currency called *Coin*.

---

## Project Overview

*Sea Life Gacha Game* is a Python Flask project where users can:

- Earn coins through interaction
- Use coins to pull random marine creatures
- Collect creatures of different rarities
- View their inventory and profile
- Manage game content through an admin panel

This project follows a clean MVC-inspired structure using Flask Blueprints and service layers.

---

## Project Structures
project_root/
├─ app/
│  ├─ _init_.py
│  ├─ models.py          # Database models
│  ├─ database.py        # Database configuration
│  ├─ routes/            # Flask routes (admin, auth, game, profile)
│  ├─ services/          # Business logic (gacha, users, auth)
│  ├─ forms/             # WTForms
│  ├─ templates/         # Jinja HTML templates
│  └─ static/            # CSS, JS, images, avatars
│
├─ data/
│  └─ sea_life_gacha.db  # SQLite database
│
├─ requirements.txt
├─ run.py                # Application entry point
├─ seeds.py              # Database seed script
└─ README.md

## Technologies Used
    - Python 3
    - Flask
    - Flask-SQLAlchemy
    - SQLite
    - Jinja2
    - HTML / CSS / JavaScript

## Game Features
    - Gacha System
    - Uses Coin as the currency
    - Pulls a random marine creature based on rarity probabilities
    - All available creatures are included in the gacha pool

## Currency
    - Coin
    - Obtained through user interaction (clicking)
    - Used to perform gacha pulls

## User Features
    - User authentication
    - View profile and inventory
    - View collected creatures, their descriptions, and rarities

## Admin Features
    - Add, edit, and delete creatures/missions
    - Activate or deactivate creatures/missions
    - Manage missions, creatures, and announcements
    - Import and export creature/mission data via JSON

## User Roles
    - User
    - Earn coins
    - Pull creatures
    - View inventory and profile

## Admin Features
    - Add, edit, and delete creatures/mission
    - Activate or deactivate creatures/mission
    - Manage missions, creature and announcements
    - Import and export creature/mission data via JSON


## Instructions
1. Clone the repository:
git clone -b refactor/project-structure https://github.com/cydmgy/ACP_Final-Project.git

2. Create and activate virtual environment:
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

3. Install dependencies:
pip install -r requirements.txt

4. Seed the database:
python seeds.py

5. Run the app:
python run.py


## Contributors
Leader: De Vera, Marlorenz S.
Members:
    Magnaye, Clyde A.
    Magno Simon Peter B.
    Tirao, Gian Irvin Y.