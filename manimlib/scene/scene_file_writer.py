import numpy as np
from pydub import AudioSegment
import shutil
import subprocess as sp
import os
import sys
import platform

import manimlib.constants as consts
from manimlib.constants import FFMPEG_BIN
from manimlib.utils.config_ops import digest_config
from manimlib.utils.file_ops import guarantee_existence
from manimlib.utils.file_ops import add_extension_if_not_present
from manimlib.utils.file_ops import get_sorted_integer_files
from manimlib.utils.sounds import get_full_sound_file_path


class SceneFileWriter(object):
    CONFIG = {
        "write_to_movie": False,
        # TODO, save_pngs is doing nothing
        "save_pngs": False,
        "png_mode": "RGBA",
        "save_last_frame": False,
        "movie_file_extension": ".mp4",
        "gif_file_extension": ".gif",
        # Previous output_file_name
        # TODO, address this in extract_scene et. al.
        "file_name": None,
        "input_file_path": "",
        "output_directory": None,
        "open_file_upon_completion": False,
        "show_file_location_upon_completion": False,
        "quiet": False,
    }

    def __init__(self, scene, **kwargs):
        digest_config(self, kwargs)
        self.scene = scene
        self.init_output_directories()
        self.init_audio()

    # Output directories and files
    def init_output_directories(self):
        module_directory = self.output_directory or self.get_default_module_directory()
        scene_name = self.file_name or self.get_default_scene_name()
        if self.save_last_frame:
            if consts.VIDEO_DIR != "":
                image_dir = guarantee_existence(os.path.join(
                    consts.VIDEO_DIR,
                    module_directory,
                    "images",
                ))
            else:
                image_dir = guarantee_existence(os.path.join(
                    consts.VIDEO_OUTPUT_DIR,
                    "images",
                ))
            self.image_file_path = os.path.join(
                image_dir,
                add_extension_if_not_present(scene_name, ".png")
            )
        if self.write_to_movie:
            if consts.VIDEO_DIR != "":
                movie_dir = guarantee_existence(os.path.join(
                    consts.VIDEO_DIR,
                    module_directory,
                    self.get_resolution_directory(),
                ))
            else:
                movie_dir = guarantee_existence(consts.VIDEO_OUTPUT_DIR)
            self.movie_file_path = os.path.join(
                movie_dir,
                add_extension_if_not_present(
                    scene_name, self.movie_file_extension
                )
            )
            self.gif_file_path = os.path.join(
                movie_dir,
                add_extension_if_not_present(
                    scene_name, self.gif_file_extension
                )
            )
            self.partial_movie_directory = guarantee_existence(os.path.join(
                movie_dir,
                "partial_movie_files",
                scene_name,
            ))

    def get_default_module_directory(self):
        filename = os.path.basename(self.input_file_path)
        root, _ = os.path.splitext(filename)
        return root

    def get_default_scene_name(self):
        if self.file_name is None:
            return self.scene.__class__.__name__
        else:
            return self.file_name

    def get_resolution_directory(self):
        pixel_height = self.scene.camera.pixel_height
        frame_rate = self.scene.camera.frame_rate
        return "{}p{}".format(
            pixel_height, frame_rate
        )

    # Directory getters
    def get_image_file_path(self):
        return self.image_file_path

    def get_next_partial_movie_path(self):
        result = os.path.join(
            self.partial_movie_directory,
            "{:05}{}".format(
                self.scene.num_plays,
                self.movie_file_extension,
            )
        )
        return result

    def get_movie_file_path(self):
        return self.movie_file_path

    # Sound
    def init_audio(self):
        self.includes_sound = False

    def create_audio_segment(self):
        self.audio_segment = AudioSegment.silent()

    def add_audio_segment(self, new_segment,
                          time=None,
                          gain_to_background=None):
        if not self.includes_sound:
            self.includes_sound = True
            self.create_audio_segment()
        segment = self.audio_segment
        curr_end = segment.duration_seconds
        if time is None:
            time = curr_end
        if time < 0:
            raise Exception("Adding sound at timestamp < 0")

        new_end = time + new_segment.duration_seconds
        diff = new_end - curr_end
        if diff > 0:
            segment = segment.append(
                AudioSegment.silent(int(np.ceil(diff * 1000))),
                crossfade=0,
            )
        self.audio_segment = segment.overlay(
            new_segment,
            position=int(1000 * time),
            gain_during_overlay=gain_to_background,
        )

    def add_sound(self, sound_file, time=None, gain=None, **kwargs):
        file_path = get_full_sound_file_path(sound_file)
        new_segment = AudioSegment.from_file(file_path)
        if gain:
            new_segment = new_segment.apply_gain(gain)
        self.add_audio_segment(new_segment, time, **kwargs)

    # Writers
    def begin_animation(self):
        if self.write_to_movie:
            self.open_movie_pipe()

    def end_animation(self):
        if self.write_to_movie:
            self.close_movie_pipe()

    def write_frame(self, camera):
        if self.write_to_movie:
            raw_bytes = camera.get_raw_fbo_data()
            self.writing_process.stdin.write(raw_bytes)

    def save_final_image(self, image):
        file_path = self.get_image_file_path()
        image.save(file_path)
        self.print_file_ready_message(file_path)

    def finish(self):
        if self.write_to_movie:
            if hasattr(self, "writing_process"):
                self.writing_process.terminate()
            self.combine_movie_files()
        if self.save_last_frame:
            self.scene.update_frame(ignore_skipping=True)
            self.save_final_image(self.scene.get_image())
        if self.should_open_file():
            self.open_file()

    def open_movie_pipe(self):
        file_path = self.get_next_partial_movie_path()
        temp_file_path = os.path.splitext(file_path)[0] + '_temp' + self.movie_file_extension

        self.partial_movie_file_path = file_path
        self.temp_partial_movie_file_path = temp_file_path

        fps = self.scene.camera.frame_rate
        width, height = self.scene.camera.get_pixel_shape()

        command = [
            FFMPEG_BIN,
            '-y',  # overwrite output file if it exists
            '-f', 'rawvideo',
            '-s', f'{width}x{height}',  # size of one frame
            '-pix_fmt', 'rgba',
            '-r', str(fps),  # frames per second
            '-i', '-',  # The imput comes from a pipe
            '-vf', 'vflip',
            '-an',  # Tells FFMPEG not to expect any audio
            '-loglevel', 'error',
        ]
        # TODO, the test for a transparent background should not be based on
        # the file extension.
        if self.movie_file_extension == ".mov":
            # This is if the background of the exported
            # video should be transparent.
            command += [
                '-vcodec', 'qtrle',
            ]
        else:
            command += [
                '-vcodec', 'libx264',
                '-pix_fmt', 'yuv420p',
            ]
        command += [temp_file_path]
        self.writing_process = sp.Popen(command, stdin=sp.PIPE)

    def close_movie_pipe(self):
        self.writing_process.stdin.close()
        self.writing_process.wait()
        shutil.move(
            self.temp_partial_movie_file_path,
            self.partial_movie_file_path,
        )

    def combine_movie_files(self):
        # Manim renders the scene as many smaller movie files
        # which are then concatenated to a larger one.  The reason
        # for this is that sometimes video-editing is made easier when
        # one works with the broken up scene, which effectively has
        # cuts at all the places you might want.  But for viewing
        # the scene as a whole, one of course wants to see it as a
        # single piece.
        kwargs = {
            "remove_non_integer_files": True,
            "extension": self.movie_file_extension,
        }
        if self.scene.start_at_animation_number is not None:
            kwargs["min_index"] = self.scene.start_at_animation_number
        if self.scene.end_at_animation_number is not None:
            kwargs["max_index"] = self.scene.end_at_animation_number
        else:
            kwargs["remove_indices_greater_than"] = self.scene.num_plays - 1
        partial_movie_files = get_sorted_integer_files(
            self.partial_movie_directory,
            **kwargs
        )
        if len(partial_movie_files) == 0:
            print("No animations in this scene")
            return

        # Write a file partial_file_list.txt containing all
        # partial movie files
        file_list = os.path.join(
            self.partial_movie_directory,
            "partial_movie_file_list.txt"
        )
        with open(file_list, 'w') as fp:
            for pf_path in partial_movie_files:
                if os.name == 'nt':
                    pf_path = pf_path.replace('\\', '/')
                fp.write("file \'{}\'\n".format(pf_path))

        movie_file_path = self.get_movie_file_path()
        commands = [
            FFMPEG_BIN,
            '-y',  # overwrite output file if it exists
            '-f', 'concat',
            '-safe', '0',
            '-i', file_list,
            '-loglevel', 'error',
            '-c', 'copy',
            movie_file_path
        ]
        if not self.includes_sound:
            commands.insert(-1, '-an')

        combine_process = sp.Popen(commands)
        combine_process.wait()

        if self.includes_sound:
            sound_file_path = movie_file_path.replace(
                self.movie_file_extension, ".wav"
            )
            # Makes sure sound file length will match video file
            self.add_audio_segment(AudioSegment.silent(0))
            self.audio_segment.export(
                sound_file_path,
                bitrate='312k',
            )
            temp_file_path = movie_file_path.replace(".", "_temp.")
            commands = [
                "ffmpeg",
                "-i", movie_file_path,
                "-i", sound_file_path,
                '-y',  # overwrite output file if it exists
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "320k",
                # select video stream from first file
                "-map", "0:v:0",
                # select audio stream from second file
                "-map", "1:a:0",
                '-loglevel', 'error',
                # "-shortest",
                temp_file_path,
            ]
            sp.call(commands)
            shutil.move(temp_file_path, movie_file_path)
            os.remove(sound_file_path)

        self.print_file_ready_message(movie_file_path)

    def print_file_ready_message(self, file_path):
        print("\nFile ready at {}\n".format(file_path))

    def should_open_file(self):
        return any([
            self.show_file_location_upon_completion,
            self.open_file_upon_completion,
        ])

    def open_file(self):
        if self.quiet:
            curr_stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")

        current_os = platform.system()
        file_paths = []

        if self.save_last_frame:
            file_paths.append(self.get_image_file_path())
        if self.write_to_movie:
            file_paths.append(self.get_movie_file_path())

        for file_path in file_paths:
            if current_os == "Windows":
                os.startfile(file_path)
            else:
                commands = []
                if current_os == "Linux":
                    commands.append("xdg-open")
                elif current_os.startswith("CYGWIN"):
                    commands.append("cygstart")
                else:  # Assume macOS
                    commands.append("open")

                if self.show_file_location_upon_completion:
                    commands.append("-R")

                commands.append(file_path)

                FNULL = open(os.devnull, 'w')
                sp.call(commands, stdout=FNULL, stderr=sp.STDOUT)
                FNULL.close()

        if self.quiet:
            sys.stdout.close()
            sys.stdout = curr_stdout