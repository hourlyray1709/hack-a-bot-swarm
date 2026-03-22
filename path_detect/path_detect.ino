#include <Wire.h>
#include "Mona_ESP_lib.h"

// ── Tuning ────────────────────────────────────────────────────────────────────
const int   IR_THRESHOLD      = 35;
const int   BORDER_SPIN_SPD   = 100;
const int   OBS_STEER_AMOUNT  = 80;   // how much to bias away from obstacle
const float COLLISION_DIST_M  = 0.10;

// ── Command from Python ───────────────────────────────────────────────────────
// New field: predicted_left / predicted_right carry the
// dead-reckoning heading so Arduino uses it when vision is lost.
struct Command {
  int  left;
  int  right;
  int  predicted_left;   // FIX 2+3: heading toward predicted object pos
  int  predicted_right;
  bool vision_lost;      // true = use predicted motors + IR steering
};

Command current_cmd = {0, 0, 0, 0, false};

// ── Helpers ───────────────────────────────────────────────────────────────────
bool detect_ir(int sensor, int threshold) {
  return Detect_object(sensor, threshold);
}

void apply_motors(int left, int right) {
  left  = constrain(left,  -255, 255);
  right = constrain(right, -255, 255);

  if      (left >= 0 && right >= 0) { Left_mot_forward(left);   Right_mot_forward(right);  }
  else if (left <= 0 && right <= 0) { Left_mot_backward(-left); Right_mot_backward(-right);}
  else if (left > 0  && right < 0)  { Left_mot_forward(left);   Right_mot_backward(-right);}
  else                              { Left_mot_backward(-left); Right_mot_forward(right);  }
}

// FIX 1: Steer around mid-field obstacles using IR while still
// making forward progress toward the commanded heading.
// Returns modified {left, right} with obstacle repulsion blended in.
void obstacle_steer(int& left, int& right) {
  bool ir1 = detect_ir(1, IR_THRESHOLD); // far left
  bool ir2 = detect_ir(2, IR_THRESHOLD); // left
  bool ir3 = detect_ir(3, IR_THRESHOLD); // centre
  bool ir4 = detect_ir(4, IR_THRESHOLD); // right
  bool ir5 = detect_ir(5, IR_THRESHOLD); // far right

  // Centre obstacle: slow down and steer to whichever side is clearer
  if (ir3) {
    if (!ir1 && !ir2) {
      left  -= OBS_STEER_AMOUNT;  // bias right
      right += OBS_STEER_AMOUNT;
    } else {
      left  += OBS_STEER_AMOUNT;  // bias left
      right -= OBS_STEER_AMOUNT;
    }
  }

  // Left obstacle: steer right
  if (ir1 || ir2) {
    left  -= OBS_STEER_AMOUNT / 2;
    right += OBS_STEER_AMOUNT / 2;
  }

  // Right obstacle: steer left
  if (ir4 || ir5) {
    left  += OBS_STEER_AMOUNT / 2;
    right -= OBS_STEER_AMOUNT / 2;
  }
}

// ── Serial parsing ────────────────────────────────────────────────────────────
// Now expects: "L:123,R:-45,PL:100,PR:100,VL:0\n"
// PL/PR = predicted left/right motors, VL = vision_lost flag
void parse_command(String line) {
  auto extract = [&](const char* key) -> int {
    int idx = line.indexOf(key);
    if (idx < 0) return 0;
    int start = idx + strlen(key);
    int end   = line.indexOf(',', start);
    return (end < 0 ? line.substring(start) : line.substring(start, end)).toInt();
  };

  current_cmd.left           = extract("L:");
  current_cmd.right          = extract("R:");
  current_cmd.predicted_left  = extract("PL:");
  current_cmd.predicted_right = extract("PR:");
  current_cmd.vision_lost     = extract("VL:") == 1;
}

// ── Setup / Loop ──────────────────────────────────────────────────────────────
void setup() {
  Mona_ESP_init();
  Serial.begin(115200);
}

void loop() {
  // 1. Receive Python command
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    parse_command(line);
  }

  // 2. Border check — hard override, always wins
  bool front_border = detect_ir(3, IR_THRESHOLD) || detect_ir(4, IR_THRESHOLD) || detect_ir(5, IR_THRESHOLD);
  bool left_border  = detect_ir(1, IR_THRESHOLD);
  bool right_border = detect_ir(5, IR_THRESHOLD);

  if (front_border || left_border || right_border) {
    if (front_border || right_border)
      apply_motors(-BORDER_SPIN_SPD, BORDER_SPIN_SPD);
    else
      apply_motors(BORDER_SPIN_SPD, -BORDER_SPIN_SPD);

    Serial.println("STATUS:BORDER");
    delay(5);
    return;
  }

  // 3. Choose base motors depending on vision state
  int base_left, base_right;

  if (current_cmd.vision_lost) {
    // FIX 2+3: Use predicted heading toward last-known object position
    base_left  = current_cmd.predicted_left;
    base_right = current_cmd.predicted_right;
  } else {
    // Vision good: use Python's real commanded motors
    base_left  = current_cmd.left;
    base_right = current_cmd.right;
  }

  // 4. FIX 1: Blend in IR obstacle steering on top of base heading
  // This works whether vision is present or not
  obstacle_steer(base_left, base_right);

  apply_motors(base_left, base_right);
  Serial.println(current_cmd.vision_lost ? "STATUS:PREDICTED" : "STATUS:OK");
  delay(5);
}