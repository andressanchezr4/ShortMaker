# -*- coding: utf-8 -*-
"""
Created on Jul 2025

@author: andres.sanchez
"""

video_url = "https://www.youtube.com/watch?v=fWjsdhR3z3c&ab_channel=Indently"
working_directory = '/path/to/video/folder'
video_name = 'name_of_the_video_file'
language = 'es'

sm = ShortMaker(working_directory, video_url, video_name)
sm.video_and_captions_download(language = language)
sm.video_slicer(0, 5, 10, 
                0, 5, 20)
sm.add_captions()
