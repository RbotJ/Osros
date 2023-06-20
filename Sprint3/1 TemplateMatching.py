import cv2
import numpy as np

# Load the template
template = cv2.imread('Roof1mm.jpg', 0)
grayscale = cv2.imread('screenshotsscreenshot_20230618_211845.jpg', 0)
w, h = template.shape[::-1]

# Apply template matching
res = cv2.matchTemplate(grayscale, template, cv2.TM_CCOEFF_NORMED)
threshold = 0.8
loc = np.where(res >= threshold)

for pt in zip(*loc[::-1]):
    cv2.rectangle(grayscale, pt, (pt[0] + w, pt[1] + h), (0,0,255), 2)

cv2.imshow('Detected', grayscale)

cv2.waitKey(0)
cv2.destroyAllWindows()
