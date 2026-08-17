import streamlit as st
from PIL import Image
import numpy as np


st.write("Welcome to RecoSort: Driving Net-Zero Sustainability via Smart AI Sorting" )

# Display the camera input button
img_file_buffer = st.camera_input("Open Camera")

# If an image is captured, display it
if img_file_buffer is not None:
    image = Image.open(img_file_buffer)
    st.image(image, caption="Captured Image")

    frame = np.array(image)

    image.save("live_trash.jpg")
    with open("new_image.flag", "w") as f:
        f.write("1")
    st.success("image saved and sent to AI model")