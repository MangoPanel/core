from cv2.typing import MatLike
import numpy as np
import cv2
from rich.pretty import pprint
from PIL import Image, ImageDraw, ImageFont


def create_bubble_representation(
    image_bytes, text_polys, min_area, max_area, min_circularity, min_solidity
):
    polygons = list(
        map(lambda box: np.array(box, dtype=np.int32).reshape(-1, 1, 2), text_polys)
    )
    image = decode_bytes_to_cv2_image(image_bytes)
    # For some reason known only to Opencv developers I need to loop manually otherwise intersections break
    [cv2.fillPoly(image, [poly], (255, 255, 255)) for poly in polygons]
    transformed_image = transform_image(image)
    contours = image_contours(transformed_image)

    good_size_contours = [
        cnt for cnt in contours if min_area < cv2.contourArea(cnt) < max_area
    ]

    # The name might be slightly missleading
    # This is a contour index -> text polygon index dictionary
    contours_containing_text = {}

    for p, poly in enumerate(polygons):
        closest_contour_index = -1
        min_distance = float("inf")
        poly_center = center_of_poly(poly)

        for c, cnt in enumerate(good_size_contours):
            min_distance_to_cnt = shortest_distance_to_contour(cnt, poly_center)
            if 0 < min_distance_to_cnt < min_distance:
                min_distance = min_distance_to_cnt
                closest_contour_index = c

        if closest_contour_index != -1:
            if closest_contour_index not in contours_containing_text:
                contours_containing_text[closest_contour_index] = []
            contours_containing_text[closest_contour_index].append(p)

    # Finally we join it into a representation
    bubble_representation = [
        {
            "contour": cnt,
            "poly_ids": contours_containing_text[c],
            "is_bubble": cnt_circularity > min_circularity
            and cnt_solidity > min_solidity,
            "circularity": cnt_circularity,
            "solidity": cnt_solidity,
            "area": area,
            "perimeter": perimeter,
        }
        for c in contours_containing_text
        if c < len(good_size_contours)
        for cnt in (good_size_contours[c],)
        for area in (cv2.contourArea(cnt),)
        for hull in (cv2.convexHull(cnt),)
        for perimeter in (cv2.arcLength(cnt, True),)
        for cnt_solidity in (solidity(area, hull),)
        for cnt_circularity in (circularity(area, perimeter),)
    ]

    return bubble_representation


def transform_image(img):
    image_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, image_thresh = cv2.threshold(
        image_grey, 200, 255, cv2.THRESH_BINARY
    )  # TODO this could be changed for a better threshold

    # Create kernel for further morphology
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    # We use Erode because it erodes white giving the opposite effect on manga lines
    image_eroded = cv2.morphologyEx(image_thresh, cv2.MORPH_ERODE, kernel)
    return image_eroded


def image_contours(img):
    contours, hierarchy = cv2.findContours(
        img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE # TODO this needs to change as approx none is the most inefficient thing
    )
    return contours


def shortest_distance_to_contour(contour, point):
    return cv2.pointPolygonTest(contour, point, True)


def center_of_poly(poly):
    # Reshaping if needed
    if poly.ndim == 3:
        poly = poly.reshape(poly.shape[0], 2)
    M = cv2.moments(poly)
    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
    return center


def solidity(area, hull):
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area > 0 else 0
    return solidity


def circularity(area, perimeter):
    circularity = 4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0
    return circularity


def approx_contour(contour, precision):
    epsilon = precision * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    return approx


def clean_contours(image_bytes, contours, save_path):
    image = decode_bytes_to_cv2_image(image_bytes)
    cv2.drawContours(image, contours, -1, color=(0, 255, 0), thickness=cv2.FILLED)
    cv2.imwrite(save_path, image)
    # cv2.imshow("image", image)
    cv2.waitKey()


def fit_text_into_contour(image, contour, text, font, max_font_size=40, min_font_size=5, font_step=2, step_y=3, line_spacing=4):
    # Split text into words
    words = text.split(".")
    if not words:
        return []

    # determine the most extreme points along the contour
    c = contour
    cc = center_of_poly(c)
    (c_x, c_y) = cc
    cv2.circle(image, cc, 10, (255, 0, 255), -1)     # center


    extLeft = tuple(c[c[:, :, 0].argmin()][0])
    extRight = tuple(c[c[:, :, 0].argmax()][0])
    extTop = tuple(c[c[:, :, 1].argmin()][0])
    extBot = tuple(c[c[:, :, 1].argmax()][0])


    cv2.circle(image, extLeft, 5, (255, 0, 0), -1)     # Blue: leftmost
    cv2.circle(image, extRight, 5, (0, 255, 0), -1)    # Green: rightmost
    cv2.circle(image, extTop, 5, (0, 0, 255), -1)      # Red: topmost
    cv2.circle(image, extBot, 5, (255, 255, 0), -1)    # Cyan: bottommost

    cv2.line(image, extLeft, extRight, (128, 128, 128), 1, cv2.LINE_AA)
    cv2.line(image, extTop, extBot, (128, 128, 128), 1, cv2.LINE_AA)

    # Iterate over font sizes until it fits
    for font_size in range(max_font_size, min_font_size -1, -font_step):
        font_adjusted = font.font_variant(size=font_size)
        res = []
        fitted_word_count = 0
        top_y = extTop[1]

        for word in words:
            (word_length, word_height) = get_word_w_h(word, font_adjusted)

            if len(res) == 0:
                # print("First word")
                # Try to fit the first word
                current_y = top_y
                while current_y + word_height < extBot[1]:
                    fit_res = can_fit_word_at_y(word, font_adjusted, contour, current_y, extLeft, extRight, c_x)
                    if fit_res:
                        # print("Managed to fit the first word:")
                        # pprint(fit_res)
                        res.append(fit_res)
                        fitted_word_count += 1
                        break

                    current_y += step_y
                
                if len(res) > 0:
                    continue
                
                # Failed to fit the first word, try smaller font
                break
            else:
                # print("Not the first word, the logic shall change!!!")
                prev_res = res[-1]
                top_y = prev_res["y"]
                line = prev_res["word"] + f" {word}"
                (line_length, line_height) = get_word_w_h(line, font_adjusted)
                aviable_space = prev_res["aviable_space"]
                if line_length <= aviable_space:
                    res[-1] = {**prev_res, "word": line, "height": line_height, "length": line_length}
                    fitted_word_count += 1
                    # print("Managed to fit a word into the same line:")
                    # pprint(res[-1])
                    continue
                
                # Did not fit into the same line, update y to the next line
                top_y += (prev_res["height"] + line_spacing)
                
                fit_res = can_fit_word_at_y(word, font_adjusted, contour, top_y, extLeft, extRight, c_x)
                if fit_res:
                    # print("Managed to fit a word into the next line")
                    # pprint(fit_res)
                    res.append(fit_res)
                    fitted_word_count += 1
                    continue
                
                # If a word cant be fitted after or directly below then we need to decrease the font size
                break
        
        # print(fitted_word_count, len(words))
        if fitted_word_count == len(words):
            return res
    
    raise ValueError("Failed fitting the given text into the give contour for the given font and font size range")
            

def can_fit_word_at_y(word, font, contour, y, extLeft, extRight, c_x):
    (word_length, word_height) = get_word_w_h(word, font)
    bottom_y = y + word_height

    # Check if word fits within contour bounds
    coords_y = contour[:, :, 1]
    vertical_slice = points_in_range(y, bottom_y, coords_y, contour)
    if len(vertical_slice) < 2:
        return None

    slice_x = vertical_slice[:, :, 0]

    # Split into left and right halves
    slice_left = points_in_range(extLeft[0], c_x, slice_x, vertical_slice)
    slice_right = points_in_range(c_x, extRight[0], slice_x, vertical_slice)

    if len(slice_left) < 1 or len(slice_right) < 1:
        return None

    # Find most "inside" points
    most_inside_left = slice_left[slice_left[:, :, 0].argmax()][0]
    most_inside_right = slice_right[slice_right[:, :, 0].argmin()][0]

    space_between = most_inside_right[0] - most_inside_left[0]

    if word_length > space_between:
        return None

    return {
        "word": word,
        "x": most_inside_left[0],
        "y": y,
        "length": word_length,
        "height": word_height,
        "aviable_space": space_between,
        "font": font
    }


def get_word_w_h(word, font):
    # word_bbox = font.getbbox(word)
    # (left, top, right, bottom) = word_bbox
    # word_length = right - left
    # word_height = bottom - top
    # return (word_length, word_height)
    
    # More robust measurments using the drawn mask which should yield acutal pixel extents
    mask = font.getmask(word)
    return mask.size


def points_in_range(min, max, mask_points, points):
    mask = (mask_points >= min) & (mask_points <= max)
    local_points = points[mask][:, np.newaxis, :]
    return local_points

def decode_bytes_to_cv2_image(bytes: bytes) -> MatLike:
    i = np.frombuffer(bytes, np.uint8)
    image = cv2.imdecode(i, cv2.IMREAD_COLOR)
    return image

from PIL import ImageDraw

def draw_word(image, word_info, draw):
    x = word_info["x"]
    y = word_info["y"]
    text = word_info["word"]

    draw.text((x, y), text, font=word_info.get("font"), fill="black")

# DEMO
import json

with open("input/opmv30/000.png", mode="rb") as page:
    image = page.read()

image_copy = decode_bytes_to_cv2_image(image)

with open("output/000_res.json") as json_page:
    page = json.load(json_page)

text_polys = page["rec_polys"]
text = page["rec_texts"]

image_brep = create_bubble_representation(image, text_polys, 500, 1000000, 0.1, 0.2)

bubbles_raw = [item["contour"] for item in image_brep if item["is_bubble"]]
bubbles = bubbles_raw # [approx_contour(bub, 0.001) for bub in bubbles_raw]
decorative_text = [item["contour"] for item in image_brep if not item["is_bubble"]]

cv2.drawContours(
    image=image_copy,
    contours=bubbles,
    contourIdx=-1,
    color=(0, 255, 0),
    thickness=2,
    lineType=cv2.LINE_AA,
)
cv2.drawContours(
    image=image_copy,
    contours=decorative_text,
    contourIdx=-1,
    color=(0, 0, 255),
    thickness=2,
    lineType=cv2.LINE_AA,
)

# DRAW TEXT
# Convert OpenCV image (BGR) to PIL (RGB)
pil_image = Image.fromarray(cv2.cvtColor(image_copy, cv2.COLOR_BGR2RGB))
draw = ImageDraw.Draw(pil_image)

# Load a font (use a default one or try a TTF)
try:
    font = ImageFont.truetype("fonts/Inktype-MAp2J.ttf")
except IOError:
    font = ImageFont.load_default()  # Fallback

# Loop over all bubbles that are marked as "is_bubble"
for item in image_brep:
    if not item["is_bubble"]:
        continue  # Skip decorative text

    contour = item["contour"]
    poly_ids = item["poly_ids"]
    # print(f"Len of text array: {len(text)}")
    string = "Test string. String hihihi Mango PANEL Mango Manga. AAAA A. 12134sdlkasfjlsak"
    # for text_index in poly_ids:
    #     if text_index > len(text):
    #         print(f"Text index of: {text_index} is outside of range of the text array of len: {len(text)}")
    #     else:
    #         word = text[text_index]
    #         print(f"Word found: {word}")
    #         string.join(word)

    # Fit text into the contour

    try:
        res = fit_text_into_contour(
            image_copy,
            contour=contour,
            text=string,
            font=font,
            max_font_size=40,
            min_font_size=2,
            font_step=2,
            step_y=3,
            line_spacing=4
        )
    except Exception as e:
        print(f"Failed to fit text in bubble: {e}")
        continue

    # Draw each fitted word
    for word_info in res:
        draw_word(pil_image, word_info, draw)

# Convert back to OpenCV format (RGB → BGR)
final_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

# Show the result
cv2.imshow("Bubbles with Fitted Text", final_image)

cv2.imshow("bubbles", image_copy)
while True:
    res = cv2.waitKey()
    print(
        "You pressed %d (0x%x), LSB: %d (%s)"
        % (res, res, res % 256, repr(chr(res % 256)) if res % 256 < 128 else "?")
    )
    if res == 27:
        break
