from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Depends

from PIL import Image
import hashlib
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
import databases
import os
from pathlib import Path
import asyncio
from PIL import Image
from moviepy.editor import ImageSequenceClip, AudioFileClip, ImageClip , VideoFileClip
import shutil
import ffmpeg

DATABASE_URL = "sqlite:///./store.db"
database = databases.Database(DATABASE_URL)
metadata = MetaData()

register = Table(
    "register",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, index=True),
    Column("email", String, unique=True, index=True),
    Column("password", String),
)

uploaded_files = Table(
    "uploaded_files",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String, index=True),
    Column("filename", String),
    Column("filepath", String),  
)

selected_files = Table(
    "selected_files",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String, index=True),
    Column("filepath",String),
    Column("time",Integer),
)


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def hash_password(password):
    sha256 = hashlib.sha256()
    sha256.update(password.encode())
    return sha256.hexdigest()

def resize_image(image_path, output_path, size=(500, 200)):
    with Image.open(image_path) as img:
        img = img.resize(size, Image.ANTIALIAS)
        img.save(output_path)

def makingvideo(resized_image_files, image_duration, audio_path, output_directory):
    try:
        # Prepare image clips
        image_clips = []
        for resized in resized_image_files:
            img_clip = ImageClip(resized)
            image_clips.append(img_clip)
        
        # Validate image sizes
        image_sizes = [clip.size for clip in image_clips]
        if len(set(tuple(size) for size in image_sizes)) != 1:
            raise ValueError("Error: Not all images are the same size. Resize the images to a uniform size.")
        else:
            print("All images are the same size.")
        
        # Create video from image clips
        clip = ImageSequenceClip([clip.img for clip in image_clips], durations=image_duration)
        clip.fps = 24
        os.makedirs(output_directory, exist_ok=True)
        output_path = os.path.join(output_directory, "output_video.mp4")
        clip.write_videofile(output_path, codec='libx264')
        
        # Ensure the audio file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at: {audio_path}")
        print(f"Audio file located: {audio_path}")
        
        # Add audio to the video
        audio = AudioFileClip(audio_path)
        video = VideoFileClip(output_path)  # Use the correct path
        f_clip = video.set_audio(audio)
        timef = sum(image_duration)
        final_clip = f_clip.subclip(0, min(timef, audio.duration))  # Ensure no out-of-range subclip
        
        # Save final video
        finaloutput_path = os.path.join(output_directory, "finaloutput_video.mp4")
        final_clip.write_videofile(finaloutput_path, codec='libx264')
        print(f"Final video created successfully at: {finaloutput_path}")
    
    except Exception as e:
        print(f"An error occurred while creating the video: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating video: {str(e)}")


def change_properties(input_file: str, output_file: str, quality: str, resolution: str):
    quality_map = {
        'low': '24',
        'medium': '23',
        'high': '18',
        'ultra': '16'
    }
    crf = quality_map.get(quality, '23')  
    resolution_map = {
        '480p': '854x480',
        '720p': '1280x720',
        '1080p': '1920x1080',
        '1440p': '2560x1440',
        '4K': '3840x2160'
    }
    scale_resolution = resolution_map.get(resolution, '1280x720') 
    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file, vf=f'scale={scale_resolution}', crf=crf)
            .run()
        )
    except ffmpeg.Error as e:
        print(f"An error occurred: {e.stderr.decode()}")
        raise


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/", response_class=HTMLResponse)
def regform(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def postreq(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    hashed_password = hash_password(password)
    query = register.insert().values(name=name, email=email, password=hashed_password)
    await database.execute(query)
    return RedirectResponse(url=f"/user/{name}/upload", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    hashed_password = hash_password(password)
    query = register.select().where(
        (register.c.name == name) &
        (register.c.email == email) &
        (register.c.password == hashed_password)
    )
    user = await database.fetch_one(query)
    if user:
        return RedirectResponse(url=f"/user/{name}/upload", status_code=303)
    else:
        error_message = "Invalid login credentials. Please try again."
        return templates.TemplateResponse("login.html", {"request": request, "error": error_message})

@app.get("/user/{username}", response_class=HTMLResponse)
def user_page(request: Request, username: str):
    return templates.TemplateResponse("user.html", {"request": request, "username": username})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    query = register.select()
    users = await database.fetch_all(query)
    return templates.TemplateResponse("adminlist.html", {"request": request, "users": users})

@app.get("/user/{username}/upload", response_class=HTMLResponse)
def upload(request: Request, username: str):
    return templates.TemplateResponse("upload.html", {"request": request, "username": username})



@app.post("/user/{username}/upload")
async def handle_upload(request: Request, username: str, files: List[UploadFile] = File(...)):
    upload_folder = f"static/uploads/{username}"
    Path(upload_folder).mkdir(parents=True, exist_ok=True)
    file_paths = []
    for file in files:
        file_location = f"{upload_folder}/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        resized_file_location = f"{upload_folder}/resized_{file.filename}"
        resize_image(file_location, resized_file_location)
        os.remove(file_location)
        file_paths.append(resized_file_location)
        query = uploaded_files.insert().values(username=username, filename=f"resized_{file.filename}", filepath=resized_file_location)
        await database.execute(query)
    
    return RedirectResponse(url=f"/user/{username}/select",status_code=303)




@app.get("/user/{username}/select", response_class=HTMLResponse)
async def select_files(request: Request, username: str):
    query = uploaded_files.select().where(uploaded_files.c.username == username)
    files = await database.fetch_all(query)
    audio_folder = Path("static/audio")
    audio_files = [f.name for f in audio_folder.glob("*") if f.is_file()]

    return templates.TemplateResponse("select.html", {
        "request": request,
        "username": username,
        "files": files,  
        "audio_files": audio_files
    })


@app.post("/user/{username}/select")
async def handle_select(
    request: Request,
    username: str,
    files: List[str] = Form(...),
    times: List[int] = Form(...),
    audio: str = Form(...),
):
    filepaths = []
    selected_times = []
    output_directory = f"static/videos/{username}"
    resized_image_directory = f"static/resized/{username}"

    os.makedirs(resized_image_directory, exist_ok=True)
    os.makedirs(output_directory, exist_ok=True)

    # Process files and resize them
    for index, file in enumerate(files):
        file_path = f"static/uploads/{username}/{file}"
        resized_path = f"{resized_image_directory}/{file}"
        resize_image(file_path, resized_path)
        filepaths.append(resized_path)
        selected_times.append(int(times[index]))

    # Ensure the audio file exists
    audio_file_path = f"static/audio/{audio}"
    if not os.path.exists(audio_file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Generate the video
    makingvideo(filepaths, selected_times, audio_file_path, output_directory)

    # Optionally: Insert selected files into the database
    for index, file in enumerate(files):
        query = selected_files.insert().values(
            username=username,
            filepath=filepaths[index],
            time=selected_times[index],
        )
        await database.execute(query)

    return RedirectResponse(url=f"/user/{username}/preview", status_code=303)



@app.get("/user/{username}/preview", response_class=HTMLResponse)
def see(request: Request, username: str,):
    return templates.TemplateResponse("preview.html", {"request": request, "username": username})

@app.post("/user/{username}/preview")
def handle_preview(username: str, resolution: str = Form(...), quality: str = Form(...)):
    print(f"Username: {username}, Resolution: {resolution}, Quality: {quality}")
    input_file = f'static/videos/{username}/output_video.mp4'
    output_file = f'static/videos/{username}/finalwithdetailsoutput_video.mp4'
    if not os.path.isfile(input_file):
        raise HTTPException(status_code=404, detail="Input video file not found")
    try:
        change_properties(input_file, output_file, quality, resolution)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")
    return RedirectResponse(url=f"/user/{username}/output",status_code=303)

@app.get("/user/{username}/output", response_class=HTMLResponse)
def output_page(request: Request, username: str):
    """
    Display the final video and provide a download option.
    """
    output_file_path = f"/static/videos/{username}/finalwithdetailsoutput_video.mp4"
    if not os.path.isfile(f"static/videos/{username}/finalwithdetailsoutput_video.mp4"):
        raise HTTPException(status_code=404, detail="Final video not found")

    return templates.TemplateResponse("output.html", {
        "request": request,
        "username": username,
        "video_url": output_file_path,
    })



    


