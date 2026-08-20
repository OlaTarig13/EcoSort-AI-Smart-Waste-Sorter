#include <Servo.h>

// تعريف كائن السيرفو ودبوس التوصيل
Servo sortingServo;
const int servoPin = 9;

void setup() {
  Serial.begin(9600);

  sortingServo.attach(servoPin);
  sortingServo.write(0);
}

void loop() {
  // ننتظر باستمرار وصول أمر من البايثون (بدون أي حساس)
  if (Serial.available() > 0) {
    char wasteType = Serial.read();
    wasteType = toupper(wasteType);

    // تجاهل أي بيانات إضافية زي \r أو \n
    if (wasteType == 'P' || wasteType == 'W' || wasteType == 'M' || wasteType == 'U') {

      // تنظيف أي بيانات زايدة في البفر
      while (Serial.available() > 0) { Serial.read(); }

      if (wasteType == 'P') {
        sortingServo.write(0);
        delay(3000);
      }
      else if (wasteType == 'W') {
        sortingServo.write(60);
        delay(3000);
      }
      else if (wasteType == 'M') {
        sortingServo.write(120);
        delay(3000);
      }
      else if (wasteType == 'U') {
        sortingServo.write(180);
        delay(3000);
      }

      sortingServo.write(0);
      delay(2000);
    }
  }
}