# RM Step 02: AgileX 차체 3D-LiDAR/카메라 센서 URDF 통합 및 아커만 조향 정밀 검증 가이드

본 문서는 **[프로젝트 개발 로드맵]**의 **2단계: AgileX 차체 3D-LiDAR/카메라 센서 URDF 통합 및 아커만 조향 정밀 검증 (`default.world`)**을 성공적으로 수행하기 위한 엔지니어링 상세 실행 가이드입니다.

---

## 1. 개요 및 목표

* **목표:** Gazebo 경량 기본 월드(`default.world`) 환경에서 AgileX Hunter 로봇의 URDF/Xacro 파일에 3D-LiDAR(Velodyne VLP-16 등) 센서와 RGB 카메라 링크 및 Gazebo ROS2 플러그인을 통합 장착하고, RViz2에서 3D PointCloud 및 실시간 카메라 영상 스트림 시각화와 아커만 조향 동역학을 검증합니다.
* **주요 검증 요소:**
  - AgileX Hunter URDF/Xacro 모델에 3D-LiDAR 센서 및 Vision 카메라 링크/플러그인 추가 작성
  - Gazebo 시뮬레이터 상에서 3D-LiDAR (`/points_raw` / `sensor_msgs/msg/PointCloud2`) 및 카메라 (`/camera/image_raw` / `sensor_msgs/msg/Image`) 토픽 수신 주기(Hz) 및 정상 발행 모니터링
  - RViz2를 통한 3D 포인트 클라우드 및 실시간 카메라 영상 시각화
  - `teleop_twist_keyboard`를 이용해 곡선 주행 시 전륜 아커만 조향 각도(Steering Angle) 꺾임 궤적 및 오도메트리(`/odom`) 데이터 정밀도 검증

---

## 2. 사전 환경 및 의존성 패키지

- **OS:** Ubuntu 22.04 LTS (Jammy Jellyfish)
- **ROS 2:** Humble Hawksbill
- **시뮬레이터:** Gazebo Classic (v11) & RViz2
- **대상 워크스페이스:** `~/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws`

---

## 3. 단계별 상세 실행 절차

### 3.1. [Step 2.1] 센서 패키지 및 Gazebo 3D LiDAR/카메라 플러그인 의존성 설치
터미널을 열고 3D-LiDAR(Velodyne) 메쉬/플러그인 및 카메라 영상 처리에 필요한 추가 ROS2 패키지를 설치합니다.

```bash
sudo apt update
sudo apt install -y \
  ros-humble-gazebo-plugins \
  ros-humble-velodyne-description \
  ros-humble-image-transport-plugins \
  ros-humble-rviz2
```

---

### 3.2. [Step 2.2] Hunter URDF/Xacro 파일에 3D-LiDAR 및 카메라 센서 정의 추가
`hunter_description/description` 폴더 내에 센서 전용 Xacro 파일(예: `sensors.xacro`)을 신규 작성하거나 기존 `hunter.urdf.xacro`에 링크 및 Gazebo ROS2 플러그인을 정의합니다.

#### 1) 3D-LiDAR 센서 (Velodyne VLP-16 3D PointCloud)
* **설치 위치:** 차체 상단 (`chassis` 링크 기준 Z: +0.3m, X: +0.1m)
* **Gazebo 플러그인:** `libgazebo_ros_ray_sensor.so` (또는 `libgazebo_ros_velodyne_laser.so`)
* **발행 토픽:** `/points_raw` (`sensor_msgs/msg/PointCloud2`, Frame ID: `velodyne_link`)

#### 2) Vision 카메라 센서 (RGB Camera)
* **설치 위치:** 차체 전방 (`chassis` 링크 기준 Z: +0.2m, X: +0.45m)
* **Gazebo 플러그인:** `libgazebo_ros_camera.so`
* **발행 토픽:** `/camera/image_raw` (`sensor_msgs/msg/Image`, Frame ID: `camera_link`)

---

### 3.3. [Step 2.3] RViz2 시각화 설정 프로파일 구축 (`view_hunter.rviz`)
센서 데이터를 실시간 한눈에 모니터링할 수 있도록 RViz2 설정 파일(`hunter_gazebo/config/view_hunter.rviz`)을 작성/업데이트합니다.

* **Fixed Frame:** `odom` (또는 `base_link`)
* **Display 항목 추가:**
  - `RobotModel`: 로봇 외관 3D 렌더링
  - `TF`: `odom` -> `base_link` -> `velodyne_link` / `camera_link` 프레임 트리 확인
  - `PointCloud2`: Topic = `/points_raw`, Size = 0.03m, Color Transformer = Intensity / AxisColor
  - `Image`: Topic = `/camera/image_raw`

---

### 3.4. [Step 2.4] 시뮬레이션 및 RViz2 실행 후 센서 토픽 수신율(Hz) 모니터링
Gazebo 시뮬레이션을 실행하고 RViz2 및 토픽 툴을 통해 센서 데이터 수신 상태를 검증합니다.

```bash
cd ~/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws
colcon build --symlink-install
source install/setup.bash

# 1. Gazebo 시뮬레이션 스폰 (3D-LiDAR & 카메라 통합 로봇)
ros2 launch hunter_gazebo launch_sim.launch.py

# 2. 새 터미널에서 RViz2 구동 및 센서 시각화 확인
rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz

# 3. 다른 터미널에서 센서 토픽 발행 주기(Hz) 측정
ros2 topic hz /points_raw
ros2 topic hz /camera/image_raw
```

---

### 3.5. [Step 2.5] 키보드 텔레옵 조종 및 아커만 조향 동역학 검증
키보드로 차량을 좌/우 선회 조종하며 전륜 조향각 꺾임과 오도메트리 궤적을 확인합니다.

```bash
# 1. 키보드 제어 노드 구동
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 2. 오도메트리 토픽 데이터 모니터링
ros2 topic echo /odom
```

---

## 4. 검증 체크리스트 (Verification Checklist)

| 번호 | 검증 항목 | 검증 방법 및 기준 | 통과 여부 |
|:---:|:---|:---|:---:|
| 1 | **3D-LiDAR 스폰 & 토픽** | Gazebo 차체 상단에 3D-LiDAR 모델이 정상 표시되고 `/points_raw` 토픽이 10Hz 이상 발행됨 | [ ] |
| 2 | **카메라 스폰 & 토픽** | Gazebo 차체 전방에 카메라 모델이 정상 표시되고 `/camera/image_raw` 토픽이 20~30Hz 발행됨 | [ ] |
| 3 | **RViz2 시각화** | RViz2 화면 상에서 3D 포인트 클라우드와 카메라 영상 스트림이 위치 및 프레임 오류 없이 표시됨 | [ ] |
| 4 | **아커만 조향 & 오도메트리** | 키보드 회전 조종 시 전륜 바퀴 조향각이 실시간 꺾이고 `/odom` 궤적 정보가 정상 갱신됨 | [ ] |

---

## 5. 트러블슈팅 (Troubleshooting & Known Issues)

* **문제 1: RViz2에서 PointCloud2 또는 Image 토픽 표시 시 `No transform from [velodyne_link] to [odom]` 에러가 발생하는 경우**
  - **원인:** 센서 링크와 차체(`base_link`) 간의 Static TF 좌표 변환이 `robot_state_publisher`에 등록되지 않음
  - **해결:** URDF/Xacro 파일 내 센서 joint의 `parent`를 `chassis` 또는 `base_link`로 지정하고 joint type을 `fixed`로 설정

* **문제 2: Gazebo GPU Ray 센서 사용 시 포인트 클라우드가 발행되지 않거나 시뮬레이터가 강제 종료되는 경우**
  - **원인:** 가상환경 내 GPU 그래픽 드라이버/OpenGL 하드웨어 가속 미지원
  - **해결:** Gazebo 센서 타입을 `gpu_ray` 대신 CPU 기반 `ray` 타입으로 지정하여 호환성 확보

* **문제 3: 아커만 조향 선회 시 차체 오도메트리 궤적과 전륜 꺾임 각도가 불일치하는 현상**
  - **원인:** `hunter_gazebo/config/controllers.yaml` 내 wheelbase(축거) 및 wheel_track(윤거) 파라미터 값 오차
  - **해결:** Hunter 2.0 제원 규격(Wheelbase: 0.65m, Wheel Track: 0.57m)에 맞추어 컨트롤러 파라미터 재설정
