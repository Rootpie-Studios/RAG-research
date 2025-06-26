# VSCODE using conda env
This guide assumes you have Miniconda or Anaconda already installed on your Windows machine and Visual Studio Code!

1.  **Open Anaconda Prompt:**</br>
    Search for "Anaconda Prompt" in your Windows Start menu and open it.

2.  **Navigate to your Project Directory:**</br>
    Use the `cd` command to go to the root of your project directory. For example:
    ```bash
    cd C:\ws\RAG-Research
    ```

3.  **Create the Conda Environment:**</br>
    ```bash
    conda env create .venv -f environment.yml    
    ```

4.  **Activate the Environment:**</br>
    To start using the newly created environment, activate it:
    ```bash
    conda activate ./.venv
    ```

5.  **Run VSCODE:**
    ```bash
    vscode .
    ```
    
## **Select Your Conda Environment as the Python Interpreter in VSCODE:**
This is the most important step to tell VSCODE which Python installation to use for your project.

1.  **Open the Command Palette** (<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd>) OR (<kbd>Cmd</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd>).
2.  **Type "Python: Select Interpreter" and select it.**
3.  **A list of available Python interpreters will appear.** This list should include your Conda environments. Your Conda environments typically appear as `Python X.X.X (<YOUR_ENV_NAME>: conda)`.
4.  **Select the Conda environment** you want to use for your current project.
5.  **Once selected, the chosen interpreter will be displayed in the bottom-right corner of the VS Code status bar.**

## **Open a Terminal in VSCODE and Verify Activation:**
  * Open a new terminal in VSCODE (<kbd>Ctrl + \</kbd> or View \> Terminal).
  * The terminal prompt should show the name of your active Conda environment in parentheses (e.g., `(my_project_env) C:\Users\YourUser>`). This indicates that the environment is activated within the VSCODE integrated terminal.
  * You can now run `conda` commands (e.g., `conda install <package_name>`) directly in this terminal to manage packages within your selected environment.

      * **Troubleshooting Note (Windows):** If you're using PowerShell as your default terminal in VS Code on Windows, Conda environments might not activate automatically. You might need to change your default terminal profile to Command Prompt (cmd.exe) in VS Code settings (`"terminal.integrated.defaultProfile.windows": "Command Prompt"`). Alternatively, you can always open an Anaconda Prompt outside of VS Code, activate your environment there, and then launch VS Code from that activated prompt by typing `code .`.

3, **Start Coding\!**




Open Anaconda Prompt:
Search for "Anaconda Prompt" in your Windows Start menu and open it.

Navigate to your Project Directory:
Use the cd command to go to the root of your project directory. For example:
conda env create .\.venv -f requirements.yaml
