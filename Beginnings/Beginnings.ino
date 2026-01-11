#include <TFT_eSPI.h>
#include <SPI.h>
#include <SerialTransfer.h>

#define TFT_BL 27

TFT_eSPI tft = TFT_eSPI();
TFT_eSprite spr = TFT_eSprite(&tft);
SerialTransfer myTransfer;

int stats[10];

void setup() {
    Serial.begin(115200);
    delay(500);

    myTransfer.begin(Serial);

    tft.init();
    tft.setRotation(1);

    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);

    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.setTextSize(2);
    tft.setCursor(10, 10);
    tft.println("Waiting for PC data...");

    // Sprite init
    spr.setColorDepth(8);          // less RAM (1 byte per pixel)
    spr.createSprite(320, 140);    // just enough height for our lines
    spr.setTextColor(TFT_WHITE, TFT_BLACK);
    spr.setTextSize(2);
}

void loop() {
    if (myTransfer.available()) {
        uint16_t recSize = 0;
        recSize = myTransfer.rxObj(stats, recSize);

        int cpu_load = stats[0];
        int ram_load = stats[1];
        int cpu_temp = stats[2];
        int gpu_load = stats[3];
        int gpu_temp = stats[4];

        Serial.print("RX: ");
        Serial.print(cpu_load); Serial.print(", ");
        Serial.print(ram_load); Serial.print(", ");
        Serial.print(cpu_temp); Serial.print(", ");
        Serial.print(gpu_load); Serial.print(", ");
        Serial.println(gpu_temp);

        // Draw everything into the sprite
        spr.fillSprite(TFT_BLACK);

        int y = 0;
        spr.setCursor(10, y);  spr.print("CPU Load: "); spr.print(cpu_load); spr.println("%");  y += 30;
        spr.setCursor(10, y);  spr.print("RAM: ");      spr.print(ram_load); spr.println("%");  y += 30;
        spr.setCursor(10, y);  spr.print("CPU Temp: "); spr.print(cpu_temp); spr.println("C");  y += 30;
        spr.setCursor(10, y);  spr.print("GPU Load: "); spr.print(gpu_load); spr.println("%");  y += 30;
        spr.setCursor(10, y);  spr.print("GPU Temp: "); spr.print(gpu_temp); spr.println("C");

        // Push sprite to screen in one go (smooth update)
        spr.pushSprite(0, 40);   // below the "Waiting..." text
    }
    else if (myTransfer.status < 0) {
        Serial.print("ERROR: ");
        Serial.println(myTransfer.status);
    }

    delay(5);
}