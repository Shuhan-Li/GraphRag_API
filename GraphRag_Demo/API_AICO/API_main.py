from fastapi import FastAPI, UploadFile, File, HTTPException,BackgroundTasks, WebSocket, WebSocketDisconnect,Query
import os
import uuid
import subprocess
import locale
import sqlite3
from starlette.middleware.cors import CORSMiddleware


from pydantic import BaseModel
from typing import Dict

from construct_search import global_search,local_search
from queue_func import execute_command_task


from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = FastAPI(debug=True)

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     # Log request details
#     logger.debug(f"Incoming request: {request.method} {request.url} Headers: {request.headers}")
    
#     response = await call_next(request)
    
#     # Log response status
#     logger.debug(f"Response status: {response.status_code}")
#     return response

# @app.exception_handler(Exception)
# async def custom_exception_handler(request: Request, exc: Exception):
#     logging.error(f"Request {request.method} {request.url} caused an error: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={"message": "An error occurred", "detail": str(exc)},
#     )




MAX_FILE_SIZE = 40*1024  #最大上传文件
# 定义文件上传的路径
UPLOAD_DIRECTORY = "./test/input/"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)



def ini_db():
    conn = sqlite3.connect('tasks.db',check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            status TEXT,
            result TEXT
        )
    ''')
    conn.commit()
    return conn

conn = ini_db()



    


class CommandRequest(BaseModel):
    user_id: str
    use_autotune: bool
    
@app.post("/index")
async def execute_command(request: CommandRequest, background_tasks: BackgroundTasks):
    try:
        task_id = str(uuid.uuid4())
        cursor1 = conn.cursor()
        cursor1.execute('INSERT INTO "tasks" (task_id, status) VALUES (?, ?)', (task_id, "in Queue"))

        conn.commit()
 
        task = execute_command_task.apply_async(args=[request.user_id, request.use_autotune, task_id])

        

        # Return the task ID to the client for status checking
        return {"task_id": task_id, "status": "in Queue"}
   
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



#### 查询indexing状态####
@app.get("/status/")
async def get_status(task_id: str = Query(..., description="The ID of the task")):
    cursor = conn.cursor()
    cursor.execute("SELECT status, result FROM tasks WHERE task_id = ?", (task_id,))
    task = cursor.fetchone()

    if task:
        status, result = task
        return {"task_id": task_id, "status": status, "result": result}
    else:
        raise HTTPException(status_code=404, detail="Task not found")


# @app.websocket("/ws/{task_id}")
# async def websocket_endpoint(websocket: WebSocket, task_id: str):
#     await websocket.accept()
#     try:
#         while True:
#             if task_status.get(task_id) in ["completed", "failed", "error"]:
#                 await websocket.send_text(f"Task {task_id} is {task_status[task_id]}")
#                 break
#             await websocket.send_text(f"Task {task_id} is in progress")
#             await asyncio.sleep(5)
#     except WebSocketDisconnect:
#         print(f"WebSocket for task {task_id} disconnected.")


# ####Not Working Yet####
# @app.post("/cancel/{task_id}")
# async def cancel_command(task_id: str):
#     process = tasks.get(task_id)
#     if not process:
#         raise HTTPException(status_code=404, detail="Task not found")

#     try:
#         process.terminate()
#         process.wait(timeout=5)
#         task_status[task_id] = "cancelled"
#         del tasks[task_id]
#         return {"detail": f"Task {task_id} has been cancelled"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error cancelling task: {str(e)}")




class SearchRequest(BaseModel):
    id: str
    query: str
####global search####
@app.post("/globalSearch/")
async def globalSearch (search_request: SearchRequest):
    try:
        result = await global_search(search_request.id, search_request.query)
        if "not found" in result or "Error" in result:
            raise HTTPException(status_code=400, detail=result)
        
        return {"message":result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

####local search####
@app.post("/localSearch/")
async def localSearch (search_request: SearchRequest):
    try:
        result = await local_search(search_request.id, search_request.query)
        if "not found" in result or "Error" in result:
            raise HTTPException(status_code=400, detail=result)
        
        return {"message":result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    
    try:

        if not file.filename.endswith(".txt"):
            raise HTTPException(status_code=400, detail="请上传编码格式为UTF-8的.txt文本。")
    
        file_contents = await file.read()
        if len(file_contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="请上传小于40KB的文本。")
        try:
            file_contents.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="请上传编码格式为UTF-8的.txt文本。")

        #generate doc_id
        user_id = str(uuid.uuid4())
#        user_id = str("_example_uudi_")
        #Parse file path
        UPLOAD_DIRECTORY =os.path.join("./corpus/", user_id)
        if not os.path.exists(UPLOAD_DIRECTORY):
            os.makedirs(UPLOAD_DIRECTORY)

        file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)

        
        with open(file_location, "wb") as f:
            f.write(file_contents)
        
        return {"info": f"file '{file.filename}' saved at '{file_location}',\n Please KEEP Your user_id:'{user_id}' safe!", "user_id": user_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/welcome")
async def read_root():
    return {"message": "Welcome to the Graphrag API"}