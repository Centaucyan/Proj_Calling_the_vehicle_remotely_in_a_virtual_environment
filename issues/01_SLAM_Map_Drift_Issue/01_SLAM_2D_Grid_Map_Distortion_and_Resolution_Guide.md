# Issue 01: SLAM 2D 격자 지도 작성 시 오도메트리 드리프트 및 지도 왜곡 현상 분석과 해결 방안

* **등록일:** 2026-07-31
* **관련 단계:** Step 04 (SLAM 2D 격자 지도 작성 및 검증)
* **관련 노드/패키지:** `hunter_gazebo`, `slam_toolbox`, `diff_drive_controller`, `teleop_twist_keyboard`

---

## 1. 이슈 개요 (Issue Summary)

Gazebo 시뮬레이터 상의 가상 주차장 월드(`parking_garage.world`)는 정방형 직선 외벽과 직각 기둥 구조로 이루어져 있으나, `slam_toolbox`를 통해 RViz2 상에서 작성되는 2D 점유 격자 지도(Occupancy Grid Map)가 대각선 방향으로 사선 삐뚤어짐 및 벽면/기둥 중첩 왜곡(Map Drift & Shift)되는 현상이 발생함.

![Gazebo 월드 대 RViz2 지도 비교 현상](https://user-images.githubusercontent.com/placeholder/map_drift.png)

---

## 2. 근본 원인 분석 (Root Cause Analysis)

### 2.1. 아커만 조향(Ackermann) 동역학과 차동 구동(Diff Drive) 간의 오도메트리 불일치
* **로봇 섀시 모델:** AgileX Hunter는 전륜 바퀴가 실제로 꺾이는 **아커만 조향(Ackermann Steering)** 제원임.
* **시뮬레이션 오도메트리 계산기:** 현재 `hunter_gazebo` 패키지의 기본 컨트롤러는 **`diff_drive_controller` (차동 구동 방식 - 좌우 바퀴 속도 차이로 회전)**을 사용하여 `/odom` (오도메트리) 데이터를 계산함.
* **불일치 현상:** 회전 선회(Cornering) 주행 시, 로봇 물리 엔진의 실제 꺾임각과 `diff_drive_controller`가 계산하여 퍼블리시하는 오도메트리 회전각 사이에 회전 오차(Drift)가 누적됨. 결과적으로 `slam_toolbox`가 "로봇이 이동/회전했다"고 믿는 위치와 실제 라이다 센서 빔이 바라보는 벽면 각도 사이의 갭이 발생함.

### 2.2. 고속 주행 및 급격한 수동 조향 입력
* `teleop_twist_keyboard` 제어 시 높은 선속도(Linear Velocity) 및 급격한 각속도(Angular Velocity) 조종 입력으로 인해 시뮬레이션 상 바퀴 미끄러짐(Wheel Slip)이 발생하여 오도메트리가 순식간에 수십 센티미터 이상 밀림.

---

## 3. 시스템 영향 (Impact)

* 삐뚤어지거나 벽면이 이중으로 중첩 생성된 2D 지도를 그대로 사용할 경우, 다음 단계인 **Step 05 (ROS2 Nav2 자율주행)**에서 Global Costmap 장애물 표현에 오류가 발생하여 경로 재검색(Replanning) 실패 또는 벽 충돌로 이어짐.

---

## 4. 해결 방안 및 수동 주행 노하우 (Resolution & Operation Guide)

### 4.1. 매핑 주행 시 속도 대폭 제한 (서행 주행)
* `teleop_twist_keyboard` 실행 터미널에서 **`z` 키** 또는 **`c` 키**를 수 차례 눌러 선속도(Linear Speed)를 **0.15 ~ 0.2 m/s 이하**로 제한함.

### 4.2. 아커만 궤적 기반의 완만한 곡선 선회
* 직진 구간을 길게 유지하여 외벽과 4개 기둥면을 정면/측면에서 충분히 스캔함.
* 회전 시에는 키를 연속으로 누르지 않고 타닥타닥 짧게 눌러 차량이 큰 호를 그리며 천천히 선회하도록 조종함. (급격한 제자리 회전 시도 금지)

### 4.3. 지도가 밀렸을 경우 즉시 리셋 후 재매핑
* 매핑 초기 단계에서 왜곡이 크게 시작된 경우 런치 파일(`slam_mapping.launch.py`)을 재실행하여 지도를 초기화한 후 서행 주행으로 재매핑 수행.

---

## 5. 향후 개선 방향 (Future Improvement)

* **Step 05 (Nav2 자율주행 구축 시):** 차동 구동 플래너 대신 아커만 조향 제원(최소 회전 반경 제약)을 엄격히 준수하는 **`TEB Local Planner`** 또는 **`Regulated Pure Pursuit Controller`**를 연동하여 정밀한 주행 궤적 및 위치 추정 확보 예정.
