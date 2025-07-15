Telegram Shop Bot

This is a non-commercial educational project. The author holds no responsibility for the usage of this software by third parties. Download and use at your own risk.

Installation Guide:

1. Download all project files into a folder of your choice.

2. In that folder, create a virtual environment:
   python -m venv .venv

3. Activate the virtual environment:
   On Windows:
       .venv\Scripts\activate
   On Linux/macOS:
       source .venv/bin/activate

4. Install dependencies:
   pip install -r requirements.txt

5. Run the setup script and follow the instructions:
   python setup.py

6. Start the bot:
   python main.py

   When prompted, enter the password to decrypt your .env file.

7. In Telegram, send the bot the command:
   /initadmin

   Then send the master key you specified during setup.

8. Use the following commands to navigate:
   /admin - open admin panel
   /start - open user interface

9. If you need to change the wallet address, follow the instructions in main.py.
