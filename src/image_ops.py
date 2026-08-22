import cv2  # type: ignore
from numpy import ndarray
import pytesseract


def load_image_grayscale(path: str) -> ndarray:
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return image


def crop_fixed_region(
    image: ndarray, y1: int, y2: int, x1: int, x2: int
) -> ndarray:
    return image[y1:y2, x1:x2]


def find_contours_from_grayscale(
    image: ndarray, thresh_val: int, max_val: int
) -> list:
    _ret, thresh_img = cv2.threshold(
        image, thresh_val, max_val, cv2.THRESH_BINARY
    )
    contours, _hierarchy = cv2.findContours(
        thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    return contours, thresh_img


def find_balloon_rect(
    contours: list,
    w_min: int,
    w_max: int,
    h_min: int,
    h_max: int,
) -> tuple | None:
    for contour in contours:
        x, y, largura, altura = cv2.boundingRect(contour)
        if w_min <= largura <= w_max and \
           h_min <= altura <= h_max:
            return (x, y, largura, altura)
    return None


def show_image(image: ndarray, window_name: str) -> None:
    cv2.imshow(window_name, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def extract_balloon_text(image: ndarray, rect: tuple) -> str:
    x, y, width, height = rect
    x1, y1 = x, y
    x2, y2 = x + width, y + height
    balloon_crop = crop_fixed_region(image, y1, y2, x1, x2)
    text = pytesseract.image_to_string(balloon_crop)
    return text
