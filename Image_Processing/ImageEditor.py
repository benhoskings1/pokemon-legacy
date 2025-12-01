import os
import re

import cv2
import numpy as np
import pygame as pg


class ImageEditor:
    def __init__(self, file: None | str | os.PathLike = None, pixelData=None):
        if file:
            if not os.path.exists(file):
                print("NO such file")
            head, self.fileName = os.path.split(file)
            self.image = cv2.imread(file, cv2.IMREAD_UNCHANGED)
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2BGRA)
            self.pixelData = self.image

            print(self.pixelData[0, 0, :])

        elif type(pixelData) is not None:
            self.image = pixelData
            self.pixelData = pixelData

        else:
            self.image = None
            self.pixelData = None

    def crop_transparent_borders(self, overwrite: bool = False):
        # Load image with alpha channel
        img = self.pixelData

        if img.shape[2] < 4:
            raise ValueError("Image does not have an alpha channel.")

        # Extract the alpha channel
        alpha = img[:, :, 3]

        # Find all rows and columns where alpha > 0
        coords = cv2.findNonZero(alpha)

        if coords is None:
            raise ValueError("The entire image is fully transparent.")

        # Get bounding rectangle of non-transparent area
        x, y, w, h = cv2.boundingRect(coords)

        # Crop the image
        cropped = img[y:y + h, x:x + w]

        if overwrite:
            self.pixelData = cropped

        return cropped

    def loadData(self, data):
        self.pixelData = data

    def addAlphaChannel(self, overwrite=False):
        newImage = cv2.cvtColor(self.image, cv2.COLOR_RGB2RGBA)
        if overwrite:
            self.pixelData = newImage

    def resetAlpha(self, overwrite=False):
        pixelDataCopy = self.pixelData.copy()
        for row in range(pixelDataCopy.shape[0]):
            for col in range(pixelDataCopy.shape[1]):
                pixelDataCopy[row, col, 3] = 255

        if overwrite:
            self.pixelData = pixelDataCopy

        return pixelDataCopy

    def replaceImage(self, path):
        self.image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        self.pixelData = np.array(self.image)

    def eraseColour(self, colour, overwrite=False):
        pixelDataCopy = self.pixelData.copy()

        for row in range(pixelDataCopy.shape[0]):
            for col in range(pixelDataCopy.shape[1]):
                pixel = pixelDataCopy[row, col, 0:3]
                if np.array_equal(pixel, np.array(colour)):
                    pixelDataCopy[row, col, :] = 0

        if overwrite:
            self.pixelData = pixelDataCopy

        return pixelDataCopy

    def transparent_where_color(self, color: tuple[int], overwrite=True) -> np.ndarray:
        """
        Set alpha=0 where the RGB part of the image matches the given color.

        Args:
            img (np.ndarray): Input image (RGBA, shape: HxWx4, dtype=uint8).
            color (tuple[int, int, int]): RGB color to make transparent (R, G, B).

        Returns:
            np.ndarray: New RGBA image with updated alpha channel.
        """
        img = self.pixelData

        # color = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        if img.shape[2] != 4:
            raise ValueError("Input image must have 4 channels (RGBA).")

        # Separate RGB and Alpha
        rgb = img[..., :3]
        alpha = img[..., 3]

        # Create a mask where RGB matches the target color
        mask = np.all(rgb == color, axis=-1)

        # Set alpha to 0 where mask is True
        alpha[mask] = 0

        # Merge back
        img_out = img.copy()
        img_out[..., 3] = alpha

        if overwrite:
            self.pixelData = img_out

        return img_out

    def saveImage(self, directory: os.PathLike = None, name=None):
        print(self.fileName)
        if directory:
            if not os.path.exists(directory):
                print("Making directory")
                os.mkdir(directory)

        if name:
            if directory:
                cv2.imwrite(os.path.join(directory, name), self.pixelData)
            else:
                cv2.imwrite(name, self.pixelData)
        else:
            if directory:
                cv2.imwrite(os.path.join(directory, self.fileName), self.pixelData)

        print("Image Saved")

    def resizeImage(self, size, overwrite=False):
        img = self.pixelData.copy()
        img = cv2.resize(img, size, interpolation=cv2.INTER_NEAREST)

        if overwrite:
            self.pixelData = img

    def scaleImage(self, scale, overwrite=False):
        img = self.pixelData.copy()
        size = (int(img.shape[1] * scale[0]), int(img.shape[0] * scale[1]))
        img = cv2.resize(img, size, interpolation=cv2.INTER_NEAREST)

        if overwrite:
            self.pixelData = img

    def showImage(self):
        cv2.imshow("Image", self.pixelData)
        cv2.waitKey()

    def createSurface(self, bgr=True):
        surf = pg.Surface((self.pixelData.shape[1], self.pixelData.shape[0]), pg.SRCALPHA)
        pixelArray = pg.PixelArray(surf)
        for row in range(self.pixelData.shape[0]):
            for col in range(self.pixelData.shape[1]):
                if bgr:
                    r = int(self.pixelData[row, col, 2])
                    g = int(self.pixelData[row, col, 1])
                    b = int(self.pixelData[row, col, 0])
                else:
                    r = int(self.pixelData[row, col, 0])
                    g = int(self.pixelData[row, col, 1])
                    b = int(self.pixelData[row, col, 2])

                colour = pg.Color(r, g, b, int(self.pixelData[row, col, 3]))
                pixelArray[col, row] = colour
        pixelArray.close()

        return surf


class ImageEditor2:
    def __init__(self,):
        self.image = None
        self.pixel_array = None

    def load_image(self, path):
        self.image = pg.image.load(path)
        self.image.convert_alpha()

    def erase_colour(self, colour: pg.Color | tuple[int] | list[int], overwrite=False):

        self.pixel_array = pg.PixelArray(self.image)
        self.pixel_array.replace(colour, pg.Color(*colour[0:3], 0))
        self.pixel_array.close()

        return None


if __name__ == "__main__":

    for file in [f for f in os.listdir("frames") if f.endswith(".png")]:
        editor = ImageEditor(file=os.path.join("frames", file))
        editor.scaleImage(pg.Vector2(2, 2), overwrite=True)
        editor.saveImage("frames")
    # IMAGE_REGEX = r""
    # move = "bubble"
    # target = "foe"
    # base_dir = '../assets/menu/bag/pocket_buttons/key_items'
    # base_dir = f"/Users/benhoskings/Desktop/pokemon_sprites/animations/"
    # save_dir = '../assets/menu/bag/pocket_buttons/key_items'

    # move_dir = os.path.join(base_dir, move, target)
    # files = os.listdir(base_dir)
    # files = sorted([file_name for file_name in files if re.match(IMAGE_REGEX, file_name)])
    # print(files)

    # for idx, file in enumerate(files):
    #
    #     editor = ImageEditor(file=os.path.join(base_dir, file))
    #     # editor.eraseColour([248, 232, 208], overwrite=True)
    #     # editor.eraseColour([123, 206, 239], overwrite=True)
    #     editor.saveImage(directory=base_dir)
