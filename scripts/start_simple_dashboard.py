#!/usr/bin/env python3
"""
Simplified script to start the Streamlit dashboard without database dependencies.
"""

import sys
import os
import subprocess
import argparse

def main():
    """Start the Streamlit dashboard."""
    
    parser = argparse.ArgumentParser(description='Start the fairness audit dashboard')
    parser.add_argument('--port', type=int, default=8501, help='Port to run dashboard on')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    
    args = parser.parse_args()
    
    # Get the path to the dashboard app
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    dashboard_path = os.path.join(project_root, 'src', 'dashboard', 'app.py')
    
    if not os.path.exists(dashboard_path):
        print(f"Error: Dashboard app not found at {dashboard_path}")
        sys.exit(1)
    
    # Start Streamlit using py command
    cmd = [
        'py', '-m', 'streamlit', 'run', dashboard_path,
        '--server.port', str(args.port),
        '--server.address', args.host,
        '--server.headless', 'false'
    ]
    
    print(f"Starting dashboard on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the dashboard")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nDashboard stopped")
    except FileNotFoundError:
        print("Error: Streamlit not found. Please install with: py -m pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main()