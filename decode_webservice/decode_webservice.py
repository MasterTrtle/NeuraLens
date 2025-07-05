import cv2
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse
from pycocotools import mask
from PIL import Image
import io
import numpy as np

# Create the app
app = Sanic("MinimalApp")

kernel = np.ones((3, 3), np.uint8)

# User-defined handler (you can change this)
@app.route("/mask", methods=["POST"])
async def my_handler(request: Request) -> HTTPResponse:
    data = request.json

    # Decode RLE mask to binary mask
    masks = mask.decode(data)  # returns H x W (or H x W x N if multiple masks)

    # Make sure mask is 2D
    if masks.ndim == 3:
        masks = masks[:, :, 0]

    print(np.unique(masks))

    # Convert to PIL Image
    img = (masks * 255).astype(np.uint8)  # scale to 0-255
    image_dilated = cv2.dilate(img, kernel, iterations=1)
    contour = image_dilated - img
    contour = cv2.dilate(contour, kernel, iterations=1)


    # Save image to buffer
    img = Image.fromarray((contour).astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return HTTPResponse(body=buf.getvalue(), content_type="image/png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, single_process=True)
