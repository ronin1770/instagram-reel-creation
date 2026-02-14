"""
    Name: video_automation.py
    Description: This class creates videos for provided input 
    Input contains of a json object that advises on:
    - Files in the video
    - Their durations
    - Output file name
    - It uses moviepy to execute
"""

from moviepy import *
#import numpy as np
import json,sys,os,subprocess
from config import *
from backend.logger import get_logger


class VideoAutomation:

    def __init__(self, input_json_file):
        self.input_json_file = input_json_file
        self.processing_data = {}
        self.logger = get_logger(name="instagram_reel_creation_video_automation")

    #this method creates the output video
    def process_and_create_output(self):
        #check if processing_data is not {}

        if self.processing_data == {}:
            self.logger.error("Invalid processing data in JSON file. Can't continue.")
            return False
        
        try:
            # Lower process priority to keep the system responsive
            try:
                os.nice(10)
            except Exception:
                pass

            inputs      = self.processing_data["inputs"]
            durations   = self.processing_data["durations"]
            output_file = self.processing_data["output_file_name"]

            self.logger.info(
                "Processing video config. inputs=%s output=%s",
                len(inputs),
                output_file,
            )
            
            # Resource-friendly settings
            target_width = 1440
            target_size = None
            target_fps = None
            ffmpeg_threads = 1
            ffmpeg_params = ["-filter_threads", "1", "-filter_complex_threads", "1"]
            drop_audio = True

            # Render each clip to a temp file to keep memory usage low
            temp_dir = os.path.join(OUTPUT_FOLDER, "_tmp_segments")
            os.makedirs(temp_dir, exist_ok=True)
            temp_files = []
            concat_list_path = None

            # Process each input video according to durations
            # Process each input video according to durations
            for index, video_filename in enumerate(inputs):
                duration_info = durations.get(str(index), None)
                if not duration_info:
                    continue  # Skip if no duration info for this file

                # Construct full path to the video file
                video_path = os.path.join(INPUT_FOLDER, video_filename)

                # Load and process the clip
                clip = VideoFileClip(video_path)
                if target_fps is None:
                    target_fps = clip.fps or 30
                clip = clip.subclipped(duration_info["start"], duration_info["end"])
                clip = clip.with_effects([vfx.FadeOut(1)]).resized(width=target_width)
                if target_size is None:
                    target_size = clip.size
                elif clip.size != target_size:
                    # Fallback to direct resize to ensure consistent dimensions for concat
                    clip = clip.resized(width=target_size[0], height=target_size[1])
                if drop_audio:
                    clip = clip.without_audio()

                # Write the normalized segment to disk, then close the clip
                temp_file = os.path.join(temp_dir, f"segment_{index}.mp4")
                clip.write_videofile(
                    temp_file,
                    codec="libx264",
                    audio=False,
                    fps=target_fps,
                    threads=ffmpeg_threads,
                    ffmpeg_params=ffmpeg_params,
                )
                clip.close()
                temp_files.append(temp_file)

            if not temp_files:
                self.logger.error("No clips were generated from the inputs.")
                return False

            # Concatenate using ffmpeg concat demuxer to avoid loading everything into RAM
            output_path = os.path.join(OUTPUT_FOLDER, output_file)
            concat_list_path = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_list_path, "w") as concat_file:
                for temp_file in temp_files:
                    safe_path = os.path.abspath(temp_file).replace("'", "\\'")
                    concat_file.write(f"file '{safe_path}'\n")

            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
                "-c", "copy",
                "-threads", str(ffmpeg_threads),
                output_path,
            ]
            result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                self.logger.warning("ffmpeg concat failed. Falling back to re-encode.")
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_list_path,
                    "-c:v", "libx264",
                    "-r", str(target_fps or 30),
                    "-an",
                    "-threads", str(ffmpeg_threads),
                    output_path,
                ]
                result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    self.logger.error("ffmpeg re-encode failed: %s", result.stderr)
                    return False
            return True

        except Exception as e:
            self.logger.exception("Exception in process_and_create_output: %s", str(e))
            return False
        finally:
            # Cleanup temp files/segments and concat list
            for temp_file in temp_files if "temp_files" in locals() else []:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass
            if "concat_list_path" in locals() and concat_list_path:
                try:
                    if os.path.exists(concat_list_path):
                        os.remove(concat_list_path)
                except Exception:
                    pass
            if "temp_dir" in locals():
                try:
                    if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
                except Exception:
                    pass
    
    #This method takes in the json object and creates mapping for video
    def read_video_config(self):
        # Support absolute paths (like temp files) while keeping legacy INPUT_FOLDER behavior.
        if os.path.isabs(self.input_json_file) or os.path.exists(self.input_json_file):
            file_path = self.input_json_file
        else:
            file_path = os.path.join(INPUT_FOLDER, self.input_json_file)

        try:
            with open(file_path, 'r') as file:
                self.processing_data = json.load(file)
                return  True
                
        except Exception as e:
            self.logger.exception("Exception while reading video config: %s", str(e))
            return False

"""if __name__ == "__main__":
    
    inputs = [ "d.json" ]

    for input_json_file in inputs:
        print(f"\n\nProcessing: {input_json_file}\n--------------------\n")
        va = VideoAutomation(input_json_file)
        read = va.read_video_config()

        if not read:
            print(f"Issue read or parsing config file: {input_json_file}")
            sys.exit(1)
        
        created = va.process_and_create_output()

        if not created:
            print(f"Issue creating output file.")
            sys.exit(1)"""
