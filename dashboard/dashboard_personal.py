# Boilerplate as streamlit doesn't support running multiple apps from the same file
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import dashboard.dashboard as dashboard_frontend

if __name__ == "__main__":
    dashboard_frontend.main()