import streamlit as st
from PIL import Image
import numpy as np
from ultralytics import YOLO
import os
import cv2


st.set_page_config(page_title="EcoSort AI", page_icon="♻️", layout="centered")

st.title("♻️ EcoSort AI: Smart Waste Segregation System")
st.write("Driving Net-Zero Sustainability via Edge Computer Vision & Robotics")

#upload the yolo model 
@st.cache_resource
def load_yolo_model():
    try:
        model = YOLO(best (2).pt)
        return model
    except Exception as e:
        st.error(f"[ERROR] Failed to load YOLO model: {e}")
        return None
yolo_model = load_yolo_model()

# Display the camera input button
img_file_buffer = st.camera_input("Open Camera")

# If an image is captured, display it
if img_file_buffer is not None:
    image = Image.open(img_file_buffer)
    st.image(image, caption="Captured Image")

    image.save("live_trash.jpg")
    with open("new_image.flag", "w") as f:
        f.write("1")
    st.success("image saved and sent to AI model")

    if yolo_model is None:
        st.error("\n [ERROR]: The YOLO model is not loaded, the analysis cannot be performed. ")
    else:
        st.write("\n [APP]: Analyzing Image...")
        frame = np.array(image.convert("RGB"))
    
        try:
                    # تحليل إطار الصورة المباشرة بواسطة موديل YOLOv8
                    # conf=0.4 تعني إهمال أي كائن ثقته أقل من 40%
            results = yolo_model.predict(source=frame, conf=0.4, verbose=False)
                    
            detected_material = ""
                    
                    # استخراج الكائن المكتشف صاحب أعلى نسبة ثقة
            if len(results[0].boxes) > 0:
                top_box = results[0].boxes[0]  # أعلى كائن في الترتيب
                cls_id = int(top_box.cls[0])
                confidence = float(top_box.conf[0])     
                # معرفة اسم الفئة من الموديل (paper, metal, plastic, glass...)
                detected_material = yolo_model.names[cls_id].lower()
                st.info(f"[AI YOLO]: Detected Material -> {detected_material.upper()} (Conf: {confidence:.2f})")
            else:
                st.warning("[AI YOLO]: No material detected in frame.")

            st.markdown("---")
            st.subheader("Sorting Recommendation & Hardware Command")

            servo_mapping = {
                "plastic": ("Place it in the red container", 0, 'P'),
                "paper": ("Place it in the blue container", 60, 'W'),
                "metal": ("Place it in the yellow container", 120, 'M'),
            }

            instruction, angle, cmd = servo_mapping.get(
                    detected_material, 
                    ("Place it in the black container", 180 , 'U')
            )

            col1, col2 = st.columns(2)
            with col1:
                    st.success(f"Instruction: \n{instruction}")
            with col2:
                    st.metric(label= "Simulated Servo Angle", value= f"{angle}", delta=f"Command: '{cmd}'")
        except Exception as ai_error:
            st.write(f"[ERROR] AI model call failed: {ai_error}")
