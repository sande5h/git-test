#!/bin/bash
cd /home/admin/my_new_project
# Log the current timestamp to check if the script is running
echo "$(date): Script started" >> logfile.log

# Pull the latest changes from GitHub
echo "$(date): Pulling latest changes from GitHub..." >> logfile.log
git pull origin main

# Activate the virtual environment (update the path to your virtual environment)
echo "$(date): Activating virtual environment..." >> logfile.log
source /.venv/bin/activate

# Install dependencies from requirements.txt
echo "$(date): Installing dependencies from requirements.txt..." >> logfile.log
pip install -r requirements.txt

# Run the Python script
echo "$(date): Running Python script..." >> logfile.log
python3 main.py

# Check if Python script ran successfully
if [ $? -eq 0 ]; then
    echo "$(date): Python script executed successfully." >> logfile.log
else
    echo "$(date): Error in running the Python script." >> logfile.log
    deactivate
    exit 1
fi

# Add and commit changes to git
echo "$(date): Adding changes to git..." >> logfile.log
git add .
git commit -m "Automated update at $(date)"

# Push the changes back to GitHub
echo "$(date): Pushing changes to GitHub..." >> logfile.log
git push origin main

# Deactivate the virtual environment
echo "$(date): Deactivating virtual environment..." >> logfile.log
deactivate

# End of the script
echo "$(date): Script finished" >> logfile.log
