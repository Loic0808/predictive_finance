import datetime

# Define the log file path
log_file_path = "/Users/doblerloic/Desktop/Finance_prediction_project/predictive_finance/Pipelines/time.txt"


#f = open(log_file_path, "a")
#f.write("Now the file has more content!")
#f.close()

# Get the current time
current_time = datetime.datetime.now()

# Write the current time to the log file
with open(log_file_path, "a") as log_file:
    log_file.write(f"Script ran at: {current_time}\n")


"""
/usr/bin/python3 /Users/doblerloic/Desktop/Finance_prediction_project/predictive_finance/Pipelines/Get_live_data.py


* * * * * /usr/bin/python3 /Users/doblerloic/Desktop/Finance_prediction_project/predictive_finance/Pipelines/Get_live_data.py
"""
