from PIL import ImageChops


class U2Image:
    @staticmethod
    def compare_images_sort(images):
        image1, image2 = images
        width1 = image1.size[0]
        width2 = image2.size[0]
        if width1 != width2:
            return False
        postion_a = U2Image.get_split_position(image1)
        image1.save('image1.jpg')
        postion_b = U2Image.get_split_position(image2)
        image2.save('image2.jpg')
        if postion_a and postion_b and postion_a == postion_b:
            return True
        return False

    @staticmethod
    def check_analysis(img):
        width = img.size[0]
        height = img.size[1]
        black = (0, 0, 0)
        pixel_lb = img.getpixel((0, height - 1))
        pixel_lb1 = img.getpixel((1, height - 2))
        pixel_ru = img.getpixel((width - 1, 0))
        pixel_ru1 = img.getpixel((width - 2, 1))
        pixel_rb = img.getpixel((width - 1, height - 1))
        pixel_rb1 = img.getpixel((width - 2, height - 2))
        if (pixel_lb == black and pixel_lb1 == black) or (pixel_ru == black and pixel_ru1 == black) or (
                pixel_rb == black and pixel_rb1 == black):
            return True
        return False

    @staticmethod
    def compare_images(image1, image2):
        diff = ImageChops.difference(image1, image2)
        if diff.getbbox() is None:
            return None
        diff.save('diff.jpg')
        image1.save('diff_image.jpg')
        return image1, image2

    @staticmethod
    def get_split_position(img):
        width = img.size[0]
        height = img.size[1]

        pixel_lb = img.getpixel((0, height - 1))
        pixel_ru = img.getpixel((width - 1, 0))

        x = 0
        y = 0
        if pixel_lb == (0, 0, 0):
            for w in range(1, width):
                pixel = img.getpixel((w, height - 1))
                if pixel == (0, 0, 0):
                    x += 1
                else:
                    break
        elif pixel_ru == (0, 0, 0):
            for h in range(1, height):
                pixel = img.getpixel((width - 1, h))
                if pixel == (0, 0, 0):
                    y += 1
                else:
                    break
        if x > 100 or y > 100:
            return x, y
        else:
            return None

    @staticmethod
    def split_image(img):
        width = img.size[0] - 1
        height = img.size[1] - 1
        x, y = U2Image.get_split_position(img)
        a1 = None
        a2 = None
        if x > 0:
            a1 = img.crop((0, 0, x, height - 40))
            a2 = img.crop((x, 0, width - 1, height - 40))
        else:
            a1 = img.crop((0, 0, width - 1, y - 40))
            a2 = img.crop((0, y, width - 1, height - 40))
        a1.save('a1.jpg')
        a2.save('a2.jpg')
        return a1, a2
        # for x in range(0, width):
        #     check_pass = False
        #     for i in range(100):
        #         if x + i > width:
        #             found = False
        #             break
        #         pixel = img.getpixel((x + i, height))
        #         if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
        #             check_pass = True
        #         else:
        #             check_pass = False
        #             break
        #     if check_pass:
        #         found = True
        #         split_y = height
        #         for x2 in range(100, width):
        #             pixel = img.getpixel((x2, height))
        #             if pixel[0] != 0 or pixel[1] != 0 or pixel[2] != 0:
        #                 split_x = x2
        #                 break
        #         break
        #
        # if split_x and split_y:
        #     a1 = img.crop((0, 0, split_x, split_y - 40))
        #     print('found in x')
        #     a1.save('a1.jpg')
        #     a2 = img.crop((split_x, 0, width-1, split_y - 40))
        #     a2.save('a2.jpg')
        #     return a1, a2
        #
        # for y in range(0, height):
        #     check_pass = False
        #     for i in range(100):
        #         if y + i > height:
        #             found = False
        #             break
        #         pixel = img.getpixel((width, y + i))
        #         if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
        #             check_pass = True
        #         else:
        #             check_pass = False
        #             break
        #     if check_pass:
        #         found = True
        #         split_x = width
        #         for y2 in range(100, height):
        #             pixel = img.getpixel((width, y2))
        #             if pixel[0] != 0 or pixel[1] != 0 or pixel[2] != 0:
        #                 split_y = y2
        #                 break
        #         break
        #
        # if split_x and split_y:
        #     a1 = img.crop((0, 0, split_x, split_y - 40))
        #     print('found in y')
        #     a1.save('a1.jpg')
        #     a2 = img.crop((0, split_y, width, height - 40))
        #     a2.save('a2.jpg')
        #     return a1, a2

# if __name__ == '__main__':
#     imagea = Image.open('D:/IvonWei/Downloads/u2/3.jpg')
#     a1, b1 = split_iamge(imagea)
#
#     imageb = Image.open('D:/IvonWei/Downloads/u2/5.jpg')
#     a2, b2 = split_iamge(imageb)
#     image_one = compare_images(a1, a2, 'a1c.jpg')
#     if not image_one:
#         image_one = compare_images(b1, b2, 'b1c.jpg')
