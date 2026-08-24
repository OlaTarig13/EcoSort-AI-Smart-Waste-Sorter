import streamlit as st
from PIL import Image
import numpy as np
import cv2
import time
import serial
from ultralytics import YOLO

st.set_page_config(page_title="EcoSort AI", page_icon="♻️", layout="centered")

st.title("♻️ EcoSort AI: Smart Waste Segregation System")
st.write("Driving Net-Zero Sustainability via Edge Computer Vision & Robotics")
st.write("Welcome to EcoSort: Driving Net-Zero Sustainability via Smart AI Sorting")

# ----------------------------
# الإعدادات
# ----------------------------
ARDUINO_PORT = "COM5"
MODEL_PATH = "best.pt"        # تأكد لا توجد مسافة قبل الامتداد
CONFIDENCE_THRESHOLD = 0.4

# وضع تجريبي: يشغّل الموديل حتى لو لم يتصل الأردوينو (مفيد أثناء التطوير)
DEMO_MODE_IF_NO_ARDUINO = True


# ----------------------------
# تحميل الموارد مرة واحدة فقط (Cache)
# ----------------------------
@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)


@st.cache_resource
def connect_arduino():
    ser = serial.Serial(port=ARDUINO_PORT, baudrate=9600, timeout=1)
    time.sleep(2)  # وقت مطلوب حتى يستقر اتصال Arduino بعد الفتح
    return ser


# تحميل الموديل
try:
    yolo_model = load_model()
    st.sidebar.success("[OK] YOLO model loaded successfully.")
except Exception as e:
    st.error(f"[ERROR] Failed to load YOLO model: {e}")
    st.stop()

# الاتصال بالأردوينو
arduino = None
arduino_connected = False
try:
    arduino = connect_arduino()
    arduino_connected = True
    st.sidebar.success("[OK] Arduino connected successfully")
except Exception as e:
    st.sidebar.error(f"[ERROR] Could not connect to Arduino on {ARDUINO_PORT}: {e}")
    if not DEMO_MODE_IF_NO_ARDUINO:
        st.stop()
    else:
        st.sidebar.warning("Running in DEMO mode (no Arduino commands will be sent).")


# ----------------------------
# إدارة حالة الالتقاط (لدعم زر "التقاط جديد")
# ----------------------------
if "capture_key" not in st.session_state:
    st.session_state.capture_key = 0

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 التقاط جديد"):
        st.session_state.capture_key += 1
        st.rerun()

img_file_buffer = st.camera_input(
    "Open the camera and capture a waste image",
    key=f"camera_{st.session_state.capture_key}",
)

# ----------------------------
# المعالجة عند التقاط صورة
# ----------------------------
if img_file_buffer is not None:
    image = Image.open(img_file_buffer)
    st.image(image, caption="الصورة الملتقطة")

    # تحويل الصورة مباشرة من الذاكرة (بدون حفظ على القرص)
    frame_rgb = np.array(image.convert("RGB"))
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    st.write("[APP]: A new image has been received, analysis is underway...")

    detected_material = ""
    confidence = 0.0

    try:
        results = yolo_model.predict(source=frame_bgr, conf=CONFIDENCE_THRESHOLD, verbose=False)

        if len(results[0].boxes) > 0:
            top_box = results[0].boxes[0]  # أعلى كائن ثقة في الترتيب
            cls_id = int(top_box.cls[0])
            confidence = float(top_box.conf[0])
            detected_material = yolo_model.names[cls_id].lower()
            st.write(f"[AI YOLO]: The detected material -> **{detected_material.upper()}** (Confidence: {confidence:.2f})")

            # عرض الصورة مع صناديق الاكتشاف
            annotated = results[0].plot()
            annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            st.image(annotated_rgb, caption="Detection Result")
        else:
            st.write("[AI YOLO]: No material detected in the image.")

    except Exception as ai_error:
        st.error(f"[ERROR] Failed to run AI model: {ai_error}")

    # تحديد الأمر المناسب للأردوينو
    if "plastic" in detected_material:
        command, label = b'P', "Plastic (P)"
    elif "paper" in detected_material:
        command, label = b'W', "Paper (W)"
    elif "metal" in detected_material:
        command, label = b'M', "Metal (M)"
    else:
        command, label = b'U', "Unknown (U)"
        st.warning("[WARNING] The type of material was not recognized clearly.")

    # إرسال الأمر للأردوينو (فقط إذا كان متصلًا)
    if arduino_connected and arduino is not None:
        try:
            arduino.write(command)
            st.success(f"-> The command has been sent to Arduino: Open Box {label}")

            # قراءة رد اختياري من الأردوينو للتأكيد
            time.sleep(2)
            if arduino.in_waiting > 0:
                response = arduino.readline().decode(errors="ignore").strip()
                if response:
                    st.info(f"[Arduino Response]: {response}")

        except Exception as serial_error:
            st.error(f"[ERROR] Failed to send command to Arduino: {serial_error}")
    else:
        st.info(f"[DEMO MODE] would have sent the command: Open Box {label} (without connected Arduino)")
