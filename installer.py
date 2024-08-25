import os

def upgrade_pip() -> None:
    """
    Runs windows command-console command to upgrade Python Package Manager (pip).
    """
    os.system('cmd /c "python -m pip install --upgrade pip"')

def pip_install_requirements() -> None:
    """
    Runs windows command-console command to install requirements.
    """
    os.system('cmd /c "python -m pip install -r requirements.txt"')

def pip_install():
    """
    Prepares environment and installs needed packages.
    """

    #Make sure we are in our directory.
    curr_path = os.getcwd()
    os.chdir(curr_path)

    #Upgrading and installing requirements.
    upgrade_pip()
    pip_install_requirements()