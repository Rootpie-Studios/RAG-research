import fire
import os
import subprocess
import re
import sys

# ANSI escape codes for colors
COLOR_RESET = "\033[0m"
COLOR_BLUE = "\033[94m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_CYAN = "\033[96m"


def run_script(script_name):
    # Get the directory of the current script (main.py)
    current_script_dir = os.path.dirname(__file__)

    script_path = os.path.join(current_script_dir, script_name)

    print(f"\n{COLOR_YELLOW}Running: {COLOR_RESET}{script_name}...{COLOR_RESET}")
    try:
        # Use sys.executable to ensure the script runs with the current Python interpreter
        subprocess.run(
            [sys.executable, script_name],  # Command relative to 'cwd'
            cwd=current_script_dir,  # This sets the working directory for the command
            check=True,  # Raise CalledProcessError for non-zero exit codes
        )
        print(f"{COLOR_GREEN}{script_name} finished successfully.{COLOR_RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{COLOR_RED}Error running {script_path}: {e}{COLOR_RESET}")
    except FileNotFoundError:
        # This specific FileNotFoundError typically means sys.executable itself wasn't found,
        # which is highly unlikely if your script is already running.
        # More likely, if you *were* using "python", it would mean "python" wasn't in PATH.
        print(
            f"{COLOR_RED}Error: Could not find the Python interpreter at {sys.executable}. This indicates a serious issue with your Python installation.{COLOR_RESET}"
        )
    except Exception as e:
        print(f"{COLOR_RED}An unexpected error occurred: {e}{COLOR_RESET}")


def run_batch(base_name="BASELINE", tokens="512/0"):
    """
    Executes a batch run by dynamically updating 'config.py' with
    different MAX_TOKENS and OVERLAP values.\n
    Example:
        python batch_run.py --base_name=EXP1 --tokens=384/0,512/128

    Args:
        base_name (str): The base name for the version. Example: BASELINE
        tokens (str): Comma-separated list of MAX_TOKENS/OVERLAP pairs. Example: '384/0,384/100,512/120'

    """

    # Get the directory of the current script (main.py)
    current_script_dir = os.path.dirname(__file__)
    config_path = os.path.join(current_script_dir, "config.py")

    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        return

    token_list = tokens.split(",")

    for token_pair in token_list:
        try:
            max_tokens, overlap = token_pair.split("/")
            max_tokens = int(max_tokens)
            overlap = int(overlap)
        except ValueError:
            print(
                f"Invalid token format: {token_pair}. Should be 'MAX_TOKENS/OVERLAP'."
            )
            continue

        with open(config_path, "r") as f:
            config_content = f.read()

        # Update BASE_NAME_VERSION
        config_content = re.sub(
            r"BASE_NAME_VERSION\s*=\s*.*",
            f"BASE_NAME_VERSION = '{base_name}'",
            config_content,
        )

        # Update MAX_TOKENS
        config_content = re.sub(
            r"MAX_TOKENS\s*=\s*\d+", f"MAX_TOKENS = {max_tokens}", config_content
        )

        # Update OVERLAP
        config_content = re.sub(
            r"OVERLAP\s*=\s*\d+", f"OVERLAP = {overlap}", config_content
        )

        with open(config_path, "w") as f:
            f.write(config_content)

        print(f"Updated config for {base_name}")
        print("--- Running process for this configuration ---")

        run_script("parse_embedd_into_db.py")
        run_script("embedd_toml_questions.py")
        run_script("query_db_all_questions.py")
        run_script("save_plots.py")

        print("--- Process finished ---")


if __name__ == "__main__":
    fire.Fire(run_batch)
