import numpy as np
import cv2
from rich.pretty import pprint


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

    # The name might be slightlyh mnissleading
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
        img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )  # TODO RETR_TREE is overkill, could be changed for a more subtle method
    return contours


def shortest_distance_to_contour(contour, point):
    return cv2.pointPolygonTest(contour, point, True)


def center_of_poly(poly):
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


def clean_contours(image_bytes, contours, save_path):
    image = decode_bytes_to_cv2_image(image_bytes)
    cv2.drawContours(image, contours, -1, color=(0, 255, 0), thickness=cv2.FILLED)
    cv2.imwrite(save_path, image)
    # cv2.imshow("image", image)
    cv2.waitKey()

def write_into_contours(contours, text):
    print("===Contours n text of a page===\n")
    pprint(contours)
    pprint(text)
    print("\n")

def fit_text_into_contour(contour, text):
    ...

def decode_bytes_to_cv2_image(bytes):
    i = np.frombuffer(bytes, np.uint8)
    image = cv2.imdecode(i, cv2.IMREAD_COLOR)
    return image



# DEMO
# image = cv2.imread("input/test/002.png")
# if image is None:
#     raise FileNotFoundError("Could not find the requested image!")
# image_copy = image.copy()
#
# with open("output/002_res.json") as json_page:
#     page = json.load(json_page)
#
# text_polys = page["rec_polys"]
# text = page["rec_texts"]
#
# image_brep = create_bubble_representation(image, text_polys, 500, 50000, 0.2, 0.2)
#
# bubbles = [item["contour"] for item in image_brep if item["is_bubble"]]
# decorative_text = [item["contour"] for item in image_brep if not item["is_bubble"]]
#
# cv2.drawContours(image=image_copy, contours=bubbles, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
# cv2.drawContours(image=image_copy, contours=decorative_text, contourIdx=-1, color=(0, 0, 255), thickness=2, lineType=cv2.LINE_AA)
#
# cv2.imshow("bubbles", image_copy)
# cv2.waitKey()
