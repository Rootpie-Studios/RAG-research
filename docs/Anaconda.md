# Conda Setup for Windows

This guide assumes you have Miniconda or Anaconda already installed on your Windows machine.

1.  **Open Anaconda Prompt:**</br>
    Search for "Anaconda Prompt" in your Windows Start menu and open it.

2.  **Navigate to your Project Directory:**</br>
    Use the `cd` command to go to the root of your project directory. For example:
    ```bash
    cd C:\ws\MyProject
    ```

3.  **Create the Conda Environment:**</br>
    Run the following command to create a new environment named `.venv` with Python 3.13.3. The `--prefix` flag ensures it's created within your project directory.
    ```bash
    conda create --prefix ./.venv python=3.13.3 -y
    ```
    * `--prefix ./.venv`: Specifies that the environment should be created in a folder named `.venv` within your current directory.
    * `python=3.13.3`: Installs Python version 3.13.3.
    * `-y`: Automatically answers yes to prompts.

4.  **Activate the Environment:**</br>
    To start using the newly created environment, activate it:
    ```bash
    conda activate ./.venv
    ```

5.  **Verify the Installation (Optional):**</br>
    You can check the Python version to confirm the setup:
    ```bash
    python --version
    ```
    This should output `Python 3.13.3`.

6.  **Install Packages (Example):**</br>
    Now that your environment is active, you can install any necessary packages for your project. For example:
    ```bash
    pip install chromadb openai pymupdf4llm tiktoken tomlkit
    ```

### To Deactivate the Environment:

When you are done working on your project, you can deactivate the environment:

```bash
conda deactivate
```

# Reuse Conda Environment
This guide assumes you have Miniconda or Anaconda already installed on your Windows machine.

1.  **Open Anaconda Prompt:**</br>
    Search for "Anaconda Prompt" in your Windows Start menu and open it.

2.  **Navigate to your Project Directory:**</br>
    Use the `cd` command to go to the root of your project directory. For example:
    ```bash
    cd C:\ws\MyProject
    ```
3.  **Activate the Environment:**</br>
    ```bash
    conda activate ./.venv
    ```

# Create a requirements.yaml file:
``` bash
conda env export --from-history >  requirements.yaml
```

## For other person to use the environment
``` bash
conda env create -p .venv -n RAG -f requirements.yaml
```
