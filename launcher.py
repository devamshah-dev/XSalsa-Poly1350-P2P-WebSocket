import subprocess
import webbrowser
import time
import platform
import os
import sys

# --- Configuration ---
BACKEND_DIR = "backend"
FRONTEND_DIR = "frontend"
CHROME_PATH = "C:/Users/DEVAMDR/Downloads/chromium-windows-browser/chrome.exe" # Windows default

def main():
    print("--- P2P Secure Chat Launcher ---")
    chrome_executable = None
    if os.path.exists(CHROME_PATH):
        chrome_executable = CHROME_PATH
    
    
    if not chrome_executable:
        print("\n[ERROR] Google Chrome app not found at the default path.")
        sys.exit(1)

    print("\n[1] Starting backend server...")
    # Windows11 uses shell=True for 'npm'.
    use_shell = platform.system() == "Windows"
    # Popen run processes in the background
    backend_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=BACKEND_DIR,
    )
    print(f"backend process started with PID: {backend_process.pid}")

    print("\n[2] Starting frontend development server...")
    frontend_process = subprocess.Popen(
        ["npm", "start"],
        cwd=FRONTEND_DIR,
        shell=use_shell
    )
    print(f"frontend process started with PID: {frontend_process.pid}")

    print("\n[3]servers to initialize...")
    time.sleep(10)#startup-time

    print("\n[4] Launching UI now...")
    
    alice_url = "http://localhost:3000/?peer=Alice&chatWith=Bob"
    bob_url = "http://localhost:3000/?peer=Bob&chatWith=Alice"

    try:
        # register the chrome executable with the webbrowser module
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_executable))

        # opens Alice in a browser window & Bob in another window
        print(f"   -> Opening Alice's window...")
        webbrowser.get('chrome').open_new(alice_url)
        print(f"   -> Opening Bob's window...")
        subprocess.Popen([chrome_executable, "--incognito", bob_url])

        print("\n--- Project is running! ---")
        print("Press Ctrl+C in this terminal to shut down all processes.")

        #launcher running in bg.
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n--- Shutting down server ---")
        backend_process.terminate()
        frontend_process.terminate()
        print("processes are now terminated.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    main()