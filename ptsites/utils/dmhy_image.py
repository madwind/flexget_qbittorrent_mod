from PIL import ImageChops, Image

RGB_BLACK = (0, 0, 0)


def compare_images_sort(image1, image2):
    if image1.size != image2.size:
        return False

    point1 = get_split_point(image1)
    point2 = get_split_point(image2)

    if point1 and point1 == point2:
        return True
    return False


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


def remove_date_string(image: Image):
    width, height = image.size
    p = Image.new('RGB', (276, 15), (0, 0, 0))
    image.paste(p, (2, height - 32))


def compare_images(image_a: Image, image_b: Image):
    a_width, a_height = image_a.size
    image_a_compare = image_a.crop((0, 0, a_width, a_height - 45))
    b_width, b_height = image_b.size
    image_b_compare = image_b.crop((0, 0, b_width, b_height - 45))

    diff = ImageChops.difference(image_a_compare, image_b_compare)
    if diff.getbbox() is None:
        return None
    return image_a, image_b, diff


def get_split_point(image: Image):
    width, height = image.size
    blank_in_bottom_left = image.getpixel((0, height - 1)) == image.getpixel((1, height - 2)) == RGB_BLACK
    blank_in_top_right = image.getpixel((width - 1, 0)) == image.getpixel((width - 2, 1)) == RGB_BLACK

    x = 0
    y = 0
    if blank_in_bottom_left:
        for w in range(1, width):
            r, g, b = image.getpixel((w, height - 1))
            if r > 7 or g > 7 or b > 7:
                x += w
                break
    elif blank_in_top_right:
        for h in range(1, height):
            r, g, b = image.getpixel((width - 1, h))
            if r > 7 or g > 7 or b > 7:
                y += h
                break
    if x > 100 or y > 100:
        return x, y
    else:
        return None


def split_image(image):
    width, height = image.size
    x, y = get_split_point(image)
    if x > 0:
        a1 = image.crop((0, 0, x, height))
        a2 = image.crop((x, 0, width, height))
    else:
        a1 = image.crop((0, 0, width, y))
        a2 = image.crop((0, y, width, height))
    return a1, a2
