import os
import re

import pygame as pg

ANIMATION_PATH = "assets/battle/move_animations"
FRAME_REGEX = r".*.png"


def get_image_frame(file_name):
    """ Extracts the number of the frame string using regex """
    match = re.search(r".*_(\d+).png", file_name)
    if match:
        return int(match.group(1))
    else:
        return None


class BattleAnimation:
    def __init__(self, frame_dir, durations: None | int | list[int]=None,size=None, scale=None, opacity=255):
        """
        Animation helper object for defining animations of multiple frames that are contained in a directory.

        :param frame_dir: directory from which to load animation frames
        :param durations: the length in ms of the animation frames
        :param size: scale the animation frames to this size
        :param scale: scale the animation frames by this scale
        :param opacity: set the opacity of the animation frames
        """

        frame_files = sorted([f for f in os.listdir(frame_dir) if f.endswith(".png")], key=get_image_frame)
        self.frames = [pg.image.load(os.path.join(frame_dir, frame))
                       for frame in frame_files if re.match(FRAME_REGEX, frame)]

        if isinstance(durations, int):
            self.durations = [durations] * len(self.frames)
        elif isinstance(durations, list):
            if len(durations) != len(self.frames):
                raise ValueError("durations and frames must have the same length")
            self.durations = durations
        elif durations is None:
            self.durations = [15] * len(self.frames)
        else:
            raise ValueError("durations must be a int, list or None")

        if size:
            self.frames = [pg.transform.scale(frame, size) for frame in self.frames]

        elif scale:
            self.frames = [pg.transform.scale(frame, pg.Vector2(frame.get_size())*scale) for frame in self.frames]

        if opacity != 255:
            for frame in self.frames:
                frame.set_alpha(opacity)

        self.frame_pause = 15

        # self._data = zip(self.frames, self.durations)
    @property
    def _data(self):
        return zip(self.frames, self.durations)

    def __iter__(self):
        for frame, duration in self._data:
            yield frame, duration

    def __getitem__(self, idx):
        return self.frames[idx]

    def __repr__(self):
        return f"BattleAnimation(num_frames={len(self.frames)}, durations={self.durations})"


if __name__ == "__main__":
    display = pg.display.set_mode((592, 384))
    background = pg.Surface(display.get_size())
    background.fill((255, 255, 255))

    frame_path = os.path.join(ANIMATION_PATH, "growl", "friendly")

    animation = BattleAnimation(frame_dir=frame_path, size=display.get_size())

    pg.event.pump()

    while True:
        for f, d in animation:
            display.blit(background, (0, 0))
            display.blit(f, (0, 0))
            pg.display.flip()
            pg.time.wait(15)

        display.blit(background, (0, 0))
        pg.display.flip()
        pg.time.wait(1500)

