

import gradio as gr
import subprocess
import json

def upload_file(file):
    print("--------")
    print(file.name)

    file_path = file.name#[1:]
    url = "http://101.201.33.94:8000/upload/"
    curl_command = [
        "curl",
        "--location",
        url,
        "--form",
        f"file=@{file_path}"
    ]
    rst = subprocess.run(curl_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


    # Check if the upload was successful
    if rst.returncode == 0:
        response_json = json.loads(rst.stdout)
        # response_json = response.json()
        # task_id = response_json.get('task_id', 'N/A')
        # status = response_json.get('status', 'N/A')
        return response_json
    else:
        return f"Failed to upload file. Status code: {rst.returncode}\n,{rst}"

# Create a Gradio interface
iface = gr.Interface(
    fn=upload_file,
    inputs=gr.File(label="Upload File"),
    outputs=gr.Textbox(label="Response"),
    title="File Upload",
    description="Upload a file to the server and receive the task ID and status."
)

# Launch the interface
iface.launch(server_name="0.0.0.0", server_port=8003) 