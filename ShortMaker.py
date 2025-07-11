# -*- coding: utf-8 -*-
"""
Created on Jul 2025

@author: andres.sanchez
"""

from datetime import timedelta, datetime
import pysrt
import subprocess
import os
import re
from moviepy import VideoFileClip, TextClip, CompositeVideoClip,  concatenate_videoclips

class ShortMaker(object):
    def __init__(self, working_directory, video_url, video_name,
                 extension = 'mp4'):
        self.working_directory = working_directory
        self.video_url = video_url 
        self.video_name = video_name
        self.video_path = f'{self.working_directory}{self.video_name}.{extension}.webm'
    
    def parse_srt_time(self, time_str):
        return datetime.strptime(time_str, "%H:%M:%S,%f")

    def format_srt_time(self, dt):
        return dt.strftime("%H:%M:%S,%f")[:-3]
    
    def time_difference_in_seconds(self, start_time_str, end_time_str):
        fmt = "%H:%M:%S"
        start = datetime.strptime(start_time_str, fmt)
        end = datetime.strptime(end_time_str, fmt)
        delta = end - start
        
        return int(delta.total_seconds())
    
    def seconds_to_hour_minute_second(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
    
        if hours > 0:
            return f"{int(hours):02}:{int(minutes):02}:{int(remaining_seconds):02}"
        else:
            return f"{int(minutes):02}:{int(remaining_seconds):02}"
        
    def restar_y_referenciar_srt(self, srt_text, seconds_less, st_time_str, nd_time_str):
        st_time = datetime.strptime(st_time_str, "%H:%M:%S").time()
        nd_time = datetime.strptime(nd_time_str, "%H:%M:%S").time()
        
        blocks = re.split(r'\n\n+', srt_text.strip())
        kept_entries = []

        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) < 2:
                continue

            times_line = lines[1]
            text_lines = lines[2:] if len(lines) > 2 else []

            match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3})\s-->\s(\d{2}:\d{2}:\d{2},\d{3})", times_line)
            if not match:
                continue

            start_dt = self.parse_srt_time(match.group(1)) - timedelta(seconds=seconds_less)
            end_dt = self.parse_srt_time(match.group(2)) - timedelta(seconds=seconds_less)

            min_dt = datetime(1900, 1, 1)
            start_dt = max(start_dt, min_dt)
            end_dt = max(end_dt, min_dt)

            start_t = start_dt.time()
            end_t = end_dt.time()

            if start_t <= nd_time and end_t >= st_time:
                kept_entries.append((start_dt, end_dt, text_lines))

        if not kept_entries:
            return ""

        min_start = min(start for start, _, _ in kept_entries)

        output_blocks = []
        for idx, (start_dt, end_dt, text_lines) in enumerate(kept_entries, start=1):
            rel_start = start_dt - min_start
            rel_end = end_dt - min_start
            new_times_line = f"{self.format_srt_time(datetime(1900,1,1)+rel_start)} --> {self.format_srt_time(datetime(1900,1,1)+rel_end)}"
            block_str = '\n'.join([str(idx), new_times_line] + text_lines)
            output_blocks.append(block_str)

        return '\n\n'.join(output_blocks)

    def time_to_seconds(self, time_obj):
        return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000

    def create_subtitle_clips(self, subtitles, videosize, fontsize=24, 
                              font="C:/Windows/Fonts/arial.ttf", 
                              color='yellow', debug = False):
        subtitle_clips = []

        for subtitle in subtitles:
            start_time = self.time_to_seconds(subtitle.start)
            end_time = self.time_to_seconds(subtitle.end)
            duration = end_time - start_time

            video_width, video_height = videosize
            
            text_clip = TextClip(text = subtitle.text, font_size=fontsize, font=font, color=color, bg_color = 'black',size=(video_width*2, None), method='caption').with_start(start_time).with_duration(duration)
            subtitle_x_position = 'center'
            subtitle_y_position = video_height* 4 / 5 

            text_position = (subtitle_x_position, subtitle_y_position)                    
            subtitle_clips.append(text_clip.with_position(text_position))

        return subtitle_clips
    
    def video_and_captions_download(self, language = 'es', captions = True):
        
        self.vtt_path = self.video_path[:-9]
        self.srt_path = self.vtt_path[:-4] + '.srt'
        
        if os.path.exists(self.video_path) and os.path.exists(self.srt_path):
            print('Video and captions already downloaded!')
            return
        
        if not os.path.exists(self.video_path):
            command = f'yt-dlp -o {self.video_name} {self.video_url}'
            subprocess.run(command.split(' '), check=True, cwd=self.working_directory)
                    
        if captions:
            command = f'yt-dlp --write-auto-sub --sub-lang {language} -o {self.vtt_path} --skip-download {self.video_url}'
            subprocess.run(command.split(' '), check=True, cwd=self.working_directory)
    
            command = f'ffmpeg -i {self.vtt_path}.es.vtt -c:s subrip {self.srt_path}'
            subprocess.run(command.split(' '), check=True, cwd=self.working_directory)
    
    def video_slicer(self, start_hour, start_minute, start_second,
                           end_hour, end_minute, end_second):
        st = [str(i) for i in [start_hour, start_minute, start_second]]
        nd = [str(i) for i in [end_hour, end_minute, end_second]]
        
        self.starting_time = ":".join(st)
        self.ending_time = ":".join(nd)
        
        start_hour = start_hour * 60 * 60
        start_minute = start_minute * 60
        start_time = start_hour + start_minute + start_second
        
        end_hour = end_hour * 60 * 60
        end_minute = end_minute * 60
        end_time = end_hour + end_minute + end_second
        
        clip = (
            VideoFileClip(self.video_path)
            .subclipped(start_time, end_time)
            .with_volume_scaled(1)
        )
        
        
        self.path2clipped_video = self.working_directory + f'clipped_video_{self.starting_time.replace(":", "-")}_{self.ending_time.replace(":", "-")}.mp4'
        
        clip.write_videofile(self.path2clipped_video, codec='libx264')
    
    def join_fragments(self, video_list_paths):
        clips = [VideoFileClip(path) for path in video_list_paths]
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(f'{self.working_directory}video_concatenado.mp4', codec="libx264", audio_codec="aac")
    
    def add_captions(self):
        final_srt = self.srt_path[:-4] + '4clip.srt'
        time_difference = self.time_difference_in_seconds(self.starting_time, 
                                                          self.ending_time) 
        with open(final_srt, 'w') as srt_write:
            my_srt = open(self.srt_path, 'r', encoding = 'utf-8').read()
            new_srt = self.restar_y_referenciar_srt(my_srt, 
                                               time_difference, 
                                               f'{self.starting_time}', 
                                               f'{self.ending_time}')
            srt_write.write(new_srt)
        
        video = VideoFileClip(self.path2clipped_video)
        subtitles = pysrt.open(final_srt)

        output_video_file = self.path2clipped_video[:-4]+ "_subtitled.mp4"

        subtitle_clips = self.create_subtitle_clips(subtitles, video.size)
        final_video = CompositeVideoClip([video] + subtitle_clips)
        final_video.write_videofile(output_video_file)
    
