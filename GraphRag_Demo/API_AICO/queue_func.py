import subprocess
import uuid
from celery import Celery
import sqlite3
import os

import shutil
from pathlib import Path


# Configure Celery to use RabbitMQ as the broker
celery_app = Celery(
    "tasks",
    broker="amqp://root:root@localhost:5672//",  # 需要根据实际情况调整localhost地址
    backend="rpc://"  # Use the RPC backend to store task results
)

celery_app.conf.broker_connection_retry_on_startup = True

# Initialize the database connection
def ini_db():
    conn = sqlite3.connect('tasks.db', check_same_thread=False)
    return conn

conn = ini_db()


def rename_output_folder(new_name: str):
    try:
        #time.sleep(120)
        parent_dir = "/home/ecs-user/GraphRag_Demo/API_AICO/_example_uudi_/output"
        if not os.path.isdir(parent_dir):
            return "Provided directory does not exist."
        
        find_latest_command = f'ls -td /home/ecs-user/GraphRag_Demo/API_AICO/_example_uudi_/output/*/ | head -n 1'
        # Execute the command and capture the output
        latest_folder = subprocess.check_output(find_latest_command, shell=True, text=True).strip()

        print("Lastes FOlder:"+ latest_folder)

        # If no folders were found, return an error
        if not latest_folder:
            return "No folders found in the specified directory."

        # Full path of the latest folder
        latest_folder_path = os.path.join(parent_dir, latest_folder)
        print("Lastes FOlder_PATH:"+ latest_folder_path)

        # Full path for the new folder name
        new_folder_path = os.path.join(parent_dir, new_name)
        print("NEW FOlder:"+ new_folder_path)

        # Rename the folder
        os.rename(latest_folder_path, new_folder_path)

        return f"Folder renamed to {new_name}"


    except Exception as e:
        raise Exception(f"Error renaming folder: {str(e)}")


@celery_app.task(bind=True)
def execute_command_task(self, user_id: str, use_autotune:bool, task_id: str) -> str:
#    task_id = str(self.request.id)

    try:
        
        #Delete all files in Input
        input_path = Path("/home/ecs-user/GraphRag_Demo/API_AICO/_example_uudi_/input")
        source_path = Path("/home/ecs-user/GraphRag_Demo/API_AICO/corpus/"+user_id)
        cache_path = Path("/home/ecs-user/GraphRag_Demo/API_AICO/_example_uudi_/cache")

        ################################
        # #delete all chat cache before each index process
        # for file in cache_path.iterdir():
        #     if file.is_file():
        #         file.unlink()
        ################################

        #delete all txt in input file
        for file in input_path.iterdir():
            if file.is_file():
                file.unlink()

        latest_file = max(source_path.glob('*'), key=os.path.getmtime)
        shutil.copy(latest_file, input_path)


        full_path = f"./API_AICO/_example_uudi_"

        # use autotuning
        finished_tune = False
        if(use_autotune == True): 
            command = f"python3 -m graphrag.prompt_tune --root {full_path} --chunk-size 300 --config settings --output {full_path}/prompts"
            # Start the autotune
            autotune_process = subprocess.Popen(command, shell=True, cwd=r"/home/ecs-user/GraphRag_Demo")
            # Update the database with task status
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status = ?, result = ? WHERE task_id = ?", ("Prompt Tuning", "", task_id))
            conn.commit()
            # Wait for the subprocess to complete
            autotune_process.wait()
            if autotune_process.returncode == 0:
                finished_tune = True
            else:
                cursor = conn.cursor()
                cursor.execute("UPDATE tasks SET status = ?, result = ? WHERE task_id = ?", ("Prompt Tuning", "Prompt Tuning FAILED", task_id))
                conn.commit()
                raise Exception("Autotuning failed")

        else:
            finished_tune = True



        command = f"python3 -m graphrag.index --root {full_path}"

        # Start the subprocess
        process = subprocess.Popen(command, shell=True, cwd=r"/home/ecs-user/GraphRag_Demo")

        # Update the database with task status
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ?, result = ? WHERE task_id = ?", ("In Progress", "", task_id))
        conn.commit()

        # Wait for the subprocess to complete
        process.wait()

        # Update task status based on subprocess return code
        if process.returncode == 0:
            rename_output_folder(task_id)
            cursor.execute("UPDATE tasks SET status = ?, result = ? WHERE task_id = ?", ("completed", "Success", task_id))
        else:
            cursor.execute("UPDATE tasks SET status = ?, result = ? WHERE task_id = ?", ("failed", "Error", task_id))
        
        conn.commit()
        return "Task completed successfully"


    except Exception as e:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ?, result = ? WHERE task_id = ?", ("failed", str(e), task_id))
        conn.commit()
        raise e