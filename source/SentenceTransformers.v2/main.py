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


def read_config_variables():
    config_path = "config.py"
    config_vars = {}
    try:
        with open(config_path, "r") as f:
            content = f.read()
            max_tokens_match = re.search(r"MAX_TOKENS = (\d+)", content)
            overlap_match = re.search(r"OVERLAP = (\d+)", content)
            base_name_version_match = re.search(
                r'BASE_NAME_VERSION = "([^"]+)"', content
            )

            if max_tokens_match:
                config_vars["MAX_TOKENS"] = int(max_tokens_match.group(1))
            if overlap_match:
                config_vars["OVERLAP"] = int(overlap_match.group(1))
            if base_name_version_match:
                config_vars["BASE_NAME_VERSION"] = base_name_version_match.group(1)
    except FileNotFoundError:
        print(f"{COLOR_RED}Error: config.py not found.{COLOR_RESET}")
        exit()
    return config_vars


def update_config_file(variable_name, old_value, new_value):
    config_path = "config.py"
    try:
        with open(config_path, "r") as f:
            content = f.read()

        if isinstance(old_value, str):
            old_string = f'{variable_name} = "{old_value}"'
            new_string = f'{variable_name} = "{new_value}"'
        else:
            old_string = f"{variable_name} = {old_value}"
            new_string = f"{variable_name} = {new_value}"

        updated_content = content.replace(
            old_string, new_string, 1
        )  # Replace only the first occurrence

        with open(config_path, "w") as f:
            f.write(updated_content)
        print(
            f"{COLOR_BLUE}Updated {variable_name} in config.py from {old_value} to {new_value}.{COLOR_RESET}"
        )
    except Exception as e:
        print(f"{COLOR_RED}Error updating config.py: {e}{COLOR_RESET}")


def get_python_files():
    files = [
        f
        for f in os.listdir(".")
        if f.endswith(".py") and f != "main2.py" and f != "config.py"
    ]
    return sorted(files)


def display_menu(files):
    print(f"\n{COLOR_CYAN}--- Python Script ---{COLOR_RESET}")
    for key, value in files.items():
        print(f"{int(key)}. {value}{COLOR_RESET}")

    print(f"{COLOR_RED}0. Exit{COLOR_RESET}")
    print(f"{COLOR_RESET}--------------------------{COLOR_RESET}")


def run_script(script_name):
    print(f"\n{COLOR_YELLOW}Running: {COLOR_RESET}{script_name}...{COLOR_RESET}")
    try:
        # Use sys.executable to ensure the script runs with the current Python interpreter
        subprocess.run([sys.executable, script_name], check=True)
        print(f"{COLOR_GREEN}{script_name} finished successfully.{COLOR_RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{COLOR_RED}Error running {script_name}: {e}{COLOR_RESET}")
    except FileNotFoundError:
        # This specific FileNotFoundError typically means sys.executable itself wasn't found,
        # which is highly unlikely if your script is already running.
        # More likely, if you *were* using "python", it would mean "python" wasn't in PATH.
        print(
            f"{COLOR_RED}Error: Could not find the Python interpreter at {sys.executable}. This indicates a serious issue with your Python installation.{COLOR_RESET}"
        )
    except Exception as e:
        print(f"{COLOR_RED}An unexpected error occurred: {e}{COLOR_RESET}")



def main():
    current_config = read_config_variables()
    print(f"{COLOR_BLUE}Current Configuration:{COLOR_RESET}")
    for key, value in current_config.items():
        print(f"  {key}: {value}")

    change_config = input(
        f"\n{COLOR_YELLOW}Do you want to change any configuration variables ({COLOR_RESET}BASE_NAME_VERSION, MAX_TOKENS, OVERLAP{COLOR_YELLOW})? (y/n): {COLOR_RESET}"
    ).lower()
    if change_config == "y":
        new_base_name_version = input(
            f"{COLOR_YELLOW}Enter new BASE_NAME_VERSION (current: {current_config.get('BASE_NAME_VERSION')}): {COLOR_RESET}"
        )
        if new_base_name_version:
            update_config_file(
                "BASE_NAME_VERSION",
                current_config.get("BASE_NAME_VERSION"),
                new_base_name_version,
            )
            current_config["BASE_NAME_VERSION"] = new_base_name_version

        new_max_tokens = input(
            f"{COLOR_YELLOW}Enter new MAX_TOKENS (current: {current_config.get('MAX_TOKENS')}, leave blank to keep): {COLOR_RESET}"
        )
        if new_max_tokens:
            try:
                new_max_tokens = int(new_max_tokens)
                update_config_file(
                    "MAX_TOKENS", current_config.get("MAX_TOKENS"), new_max_tokens
                )
                current_config["MAX_TOKENS"] = new_max_tokens
            except ValueError:
                print(
                    f"{COLOR_RED}Invalid input for MAX_TOKENS. Keeping current value.{COLOR_RESET}"
                )

        new_overlap = input(
            f"{COLOR_YELLOW}Enter new OVERLAP (current: {current_config.get('OVERLAP')}, leave blank to keep): {COLOR_RESET}"
        )
        if new_overlap:
            try:
                new_overlap = int(new_overlap)
                update_config_file(
                    "OVERLAP", current_config.get("OVERLAP"), new_overlap
                )
                current_config["OVERLAP"] = new_overlap
            except ValueError:
                print(
                    f"{COLOR_RED}Invalid input for OVERLAP. Keeping current value.{COLOR_RESET}"
                )

    print(f"\n{COLOR_BLUE}Updated Configuration (after user input):{COLOR_RESET}")
    for key, value in current_config.items():
        print(f"  {key}: {value}")

    scripts = {
        "1": "parse_embedd_into_db.py",
        "2": "embedd_toml_questions.py",
        "3": "query_db_all_questions.py",
        "4": "save_plots.py",
    }

    while True:
        display_menu(scripts)
        try:
            choice = int(input(f"{COLOR_CYAN}Enter your choice: {COLOR_RESET}"))
            if choice == 0:
                print(f"{COLOR_GREEN}Exiting...{COLOR_RESET}")
                break
            elif 1 <= choice <= len(scripts):
                run_script(scripts[str(choice)])
            else:
                print(f"{COLOR_RED}Invalid choice. Please try again.{COLOR_RESET}")
        except ValueError:
            print(f"{COLOR_RED}Invalid input. Please enter a number.{COLOR_RESET}")


if __name__ == "__main__":
    main()
