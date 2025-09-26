import subprocess
import utils
from dotenv import load_dotenv
from os import getenv, listdir
from os.path import abspath, join, dirname, isdir
load_dotenv()

CONTACT_PAGES = utils.str_to_list(getenv("CONTACT_PAGES", ""))
MAX_WORKERS = min(int(getenv("MAX_WORKERS", "10")), len(CONTACT_PAGES))
RERUNS_ON_FAILURE = int(getenv("RERUNS_ON_FAILURE", "1"))
USE_HEADLESS = utils.str_to_bool(getenv("USE_HEADLESS", "True"))
browser_extensions_dir = join(dirname(abspath(__file__)), "browser_extensions")
bot_worker_dir = join(dirname(abspath(__file__)), "bot_worker.py")

# get all directories (non-recursively) in the browser extensions directory
browser_extensions = []
for ext_dir in listdir(browser_extensions_dir):
    full_ext_dir = join(browser_extensions_dir, ext_dir)
    if isdir(full_ext_dir):
        # récupérer le sous-dossier version (souvent un seul)
        version_dirs = [join(full_ext_dir, d) for d in listdir(full_ext_dir) if isdir(join(full_ext_dir, d))]
        if version_dirs:
            browser_extensions.append(version_dirs[0])  # prend le premier
browser_extensions = ",".join(browser_extensions)

pytest_dir = join(dirname(abspath(__file__)), "..", ".venv", "Scripts", "pytest.exe")

class Orchestrator:
    def __init__(self):
        pass
    def run_workers(self):
        if MAX_WORKERS <= 0:
            raise ValueError("MAX_WORKERS must be greater than 0")
        command = [
            pytest_dir,
            "-n", str(MAX_WORKERS),
            "--uc",
            bot_worker_dir,
            "--extension-dir" if USE_HEADLESS else "",
            browser_extensions if USE_HEADLESS else "",
            "--headless2" if USE_HEADLESS else "",
            f"--reruns={RERUNS_ON_FAILURE}"
        ]

        subprocess.run(command, check=True)  # Use check=True to raise an exception on error

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run_workers()
