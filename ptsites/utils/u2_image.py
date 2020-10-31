from PIL import ImageChops, Image

RGB_BLACK = (0, 0, 0)


class U2Image:

    @staticmethod
    def compare_images_sort(image_tuple: tuple):
        image_a, image_b = image_tuple
        if image_a.size != image_b.size:
            return False

        point_a = U2Image.get_split_point(image_a)
        point_b = U2Image.get_split_point(image_b)
        image_a.save('a_original.png')
        image_b.save('b_original.png')
        if point_a and point_a == point_b:
            return True
        return False

    @staticmethod
    def check_analysis(image: Image):
        if not image:
            return False
        width, height = image.size

        pixel_points = [(0, height - 1), (1, height - 2), (width - 1, 0), (width - 2, 1), (width - 1, height - 1),
                        (width - 2, height - 2)]
        for point in pixel_points:
            if image.getpixel(point) == RGB_BLACK:
                return True
        return False

    @staticmethod
    def remove_date(image: Image):
        width, height = image.size
        p = Image.new('RGB', (276, 15), (0, 0, 0))
        image.paste(p, (2, height - 32))

    @staticmethod
    def compare_images(image_a: Image, image_b: Image):
        a_width, a_height = image_a.size
        image_a_compare = image_a.crop((0, 0, a_width, a_height - 45))
        b_width, b_height = image_b.size
        image_b_compare = image_b.crop((0, 0, b_width, b_height - 45))

        diff = ImageChops.difference(image_a_compare, image_b_compare)
        if diff.getbbox() is None:
            return None
        diff.save('diff.jpg')
        image_a_compare.save('a_diff.jpg')
        image_b_compare.save('b_diff.jpg')
        return image_a, image_b

    @staticmethod
    def get_split_point(image: Image):
        width, height = image.size
        blank_in_bottom_left = image.getpixel((0, height - 1)) == image.getpixel((1, height - 2)) == RGB_BLACK
        blank_in_top_right = image.getpixel((width - 1, 0)) == image.getpixel((width - 2, 1)) == RGB_BLACK

        x = 0
        y = 0
        if blank_in_bottom_left:
            for w in range(1, width):
                r, g, b = image.getpixel((w, height - 1))
                if r > 5 or g > 5 or b > 5:
                    x += w
                    break
        elif blank_in_top_right:
            for h in range(1, height):
                r, g, b = image.getpixel((width - 1, h))
                if r > 5 or g > 5 or b > 5:
                    y += h
                    break
        if x > 100 or y > 100:
            return x, y
        else:
            return None

    @staticmethod
    def split_image(image):
        width, height = image.size
        x, y = U2Image.get_split_point(image)
        if x > 0:
            a1 = image.crop((0, 0, x, height))
            a2 = image.crop((x, 0, width, height))
        else:
            a1 = image.crop((0, 0, width, y))
            a2 = image.crop((0, y, width, height))
        return a1, a2
