# instagram-reel-creation

## Prerequisites (Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg redis-server
```

MongoDB server is required for the `instagram_reel_creator` database.

## Environment

Create `.env` in the repo root:

```
MONGODB_URI=mongodb://localhost:27017
LOG_LOCATION=./log/backend.log
REDIS_URL=redis://localhost:6379/1
OUTPUT_FILES_LOCATION=./outputs
```

## Run the API

```bash
pip install -r requirements.txt

uvicorn main:app --reload --app-dir backend
```

## Run the worker

```bash
cd /usr/local/development/instagram-reel-creation
```


```bash
arq backend.workers.video_maker.WorkerSettings
```

## Sample cURL

Create a video:

```bash
curl -X POST http://127.0.0.1:8000/videos \
  -H "Content-Type: application/json" \
  -d '{
    "video_title": "My first reel",
    "video_introduction": "Short intro",
    "video_tags": ["travel", "daily"],
    "active": true
  }'
```

List videos:

```bash
curl -X GET http://127.0.0.1:8000/videos
```

Get a video by id:

```bash
curl -X GET http://127.0.0.1:8000/videos/<video_id>
```

Update a video:

```bash
curl -X PATCH http://127.0.0.1:8000/videos/<video_id> \
  -H "Content-Type: application/json" \
  -d '{
    "video_title": "Updated reel title",
    "active": false
  }'
```

Delete a video:

```bash
curl -X DELETE http://127.0.0.1:8000/videos/<video_id>
```

Enqueue a video for processing:

```bash
curl -X POST http://127.0.0.1:8000/videos/<video_id>/enqueue
```

Create a video part:

```bash
curl -X POST http://127.0.0.1:8000/video-parts \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "<video_id_from_create>",
    "file_part_name": "clip_01.mp4",
    "part_number": 1,
    "file_location": "/absolute/path/to/clip_01.mp4",
    "start_time": "00:00:40",
    "end_time": "00:00:50",
    "selected_duration": 8.0,
    "active": true
  }'
```

List video parts:

```bash
curl -X GET http://127.0.0.1:8000/video-parts
```

Get a video part by id:

```bash
curl -X GET http://127.0.0.1:8000/video-parts/<video_parts_id>
```

Update a video part:

```bash
curl -X PATCH http://127.0.0.1:8000/video-parts/<video_parts_id> \
  -H "Content-Type: application/json" \
  -d '{
    "file_part_name": "clip_01_trimmed.mp4",
    "selected_duration": 7.5
  }'
```

Delete a video part:

```bash
curl -X DELETE http://127.0.0.1:8000/video-parts/<video_parts_id>
```
