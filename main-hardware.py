import cv2
import serial
import time
from ultralytics import YOLO
import os

try:
    yolo_model = YOLO("best (2).pt")
    print("[OK] YOLO model loaded successfully.")
except Exception as e:
    print(f"[ERROR] Failed to load YOLO model: {e}")
    exit()

# 1. Setup Arduino Connection
arduino_port = "COM5"  # CHANGE THIS TO YOUR ACTUAL ARDUINO COM PORT
try:
    arduino = serial.Serial(port=arduino_port, baudrate=9600, timeout=1)
    time.sleep(2)  # Wait 2 seconds for connection stability
    print("[OK] Arduino connected successfully.")
except Exception as e:
    print(f"[ERROR] Could not find Arduino on {arduino_port}. Check connection/port number.")
    exit()

FLAG_FILE = "new_image.flag"
IMAGE_FILE = "live_trash.jpg"
try:
   while True:
    if os.path.exists(FLAG_FILE):
        print("\n[APP]: New image received from interface, Analyzing...")

        frame = cv2.imread(IMAGE_FILE)
        if frame is not None:          
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
                    print(f"[AI YOLO]: Detected Material -> {detected_material.upper()} (Conf: {confidence:.2f})")
                else:
                    print("[AI YOLO]: No material detected in frame.")

            except Exception as ai_error:
                print(f"[ERROR] AI model call failed: {ai_error}")
                detected_material = ""

                    # Send command back to Arduino based on a strict match
            if "plastic" in detected_material:
                    command = b'P'
                    label = "Plastic bin (P)"
            elif "paper" in detected_material:
                    command = b'W'
                    label = "Paper bin (W)"
            elif "glass" in detected_material:
                command = b'G'
                label = "Glass bin (G)"
            else:
                command = b'U'
                label = "Unknown (U)"
                print("[WARNING] Material type not clearly recognized.")

            arduino.write(command)
            print(f"-> Sending to Arduino: Open {label}")

                    # Clear any leftover bytes so the next CAPTURE starts clean

        else:
             print("[ERROR] Could not read image file")
        os.remove(FLAG_FILE)
    time.sleep(0.5)


except KeyboardInterrupt:
    print("\n[STOP]: Program stopped by user...")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
finally:
    if 'arduino' in locals() and arduino.is_open:
        arduino.close()
    print("[OK] Ports cleaned and closed successfully.")
