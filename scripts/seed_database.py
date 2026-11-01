import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.seed_data import seed_database

if __name__ == "__main__":
    seed_database()
    print("AgentGuard Database successfully seeded with baseline agents, roles, and permissions!")
