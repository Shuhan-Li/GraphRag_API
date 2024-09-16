import os

file_path = "/home/ecs-user/tmp/gradio/b91d49ff88605dfaa497661bcab64ef12f4870367d58278368aacf90133a8655/bc-4k.txt"

# Check if the file can be accessed
if not os.path.isfile(file_path):
    print("File is not accessible or doesn't exist.")
elif not os.access(file_path, os.R_OK):
    print("File is not readable.")
else:
    print("File exists and is accessible.")
    with open(file_path, 'rb') as f:
        content = f.read()
        print("File read successfully.")
