import http.client
import mimetypes
from codecs import encode
file_path = "/home/ecs-user/tmp/gradio/b91d49ff88605dfaa497661bcab64ef12f4870367d58278368aacf90133a8655/bc-4k.txt"#tmp/gradio/b91d49ff88605dfaa497661bcab64ef12f4870367d58278368aacf90133a8655/bc-4k.txt"
conn = http.client.HTTPConnection("101.201.33.94", 8000)
dataList = []
boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
dataList.append(encode('--' + boundary))
dataList.append(encode('Content-Disposition: form-data; name=file; filename={0}'.format(file_path)))


fileType = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
dataList.append(encode('Content-Type: {}'.format(fileType)))
dataList.append(encode(''))

with open(file_path, 'rb') as f:
    dataList.append(f.read())
dataList.append(encode('--'+boundary+'--'))
dataList.append(encode(''))
body = b'\r\n'.join(dataList)
payload = body
headers = { 'Content-type': 'multipart/form-data; boundary={}'.format(boundary)}
conn.request("POST", "/upload/", payload, headers)
res = conn.getresponse()
data = res.read()
rst = data.decode("utf-8") 

# # Open the file in binary mode and upload it using the requests library
# with open(file.name, 'rb') as f:
#     files = {'file': f}
#     response = requests.post(upload_url, files=files)

# Check if the upload was successful
if res.status == 200:
    # response_json = response.json()
    # task_id = response_json.get('task_id', 'N/A')
    # status = response_json.get('status', 'N/A')
    print( rst)
else:
    print( f"Failed to upload file. Status code: {res.status}\n,{rst}")