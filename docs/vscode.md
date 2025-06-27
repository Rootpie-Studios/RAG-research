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
    conda env create -p .venv -f environment.yml
    ```

4.  **Activate the Environment:**</br>
    To start using the newly created environment, activate it:
    ```bash
    conda activate .\.venv
    ```

5.  **Run VSCODE:**
    ```bash
    code .
    ```
    
## **Select Your Conda Environment as the Python Interpreter in VSCODE:**
This is the most important step to tell VSCODE which Python installation to use for your project.
  * **Open the Command Palette** (<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd>) OR (<kbd>Cmd</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd>).</br>
  * Type "Python: Select Interpreter" and select it.</br>
  * A list of available Python interpreters will appear. This list should include your Conda environments. Your Conda environments typically appear as `Python X.X.X ('.venv': conda)`.</br>
  * Select the Conda environment you want to use for your current project.</br>
  * Once selected, the chosen interpreter will be displayed in the bottom-right corner of the VS Code status bar.</br>

## **Open a Terminal in VSCODE and Verify Activation:**
  * Open a new terminal in VSCODE (<kbd>Ctrl + \</kbd> or View \> Terminal).
  * The terminal prompt should show the name of your active Conda environment in parentheses (e.g., `(my_project_env) C:\Users\YourUser>`). This indicates that the environment is activated within the VSCODE integrated terminal.
  * You can now run `conda` commands (e.g., `conda install <package_name>`) directly in this terminal to manage packages within your selected environment.


