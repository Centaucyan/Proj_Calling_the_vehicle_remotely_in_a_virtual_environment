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

센서를 추가하는 방법은 **[방법 A: 신규 전용 파일 분리 (추천 🌟)]**와 **[방법 B: 기존 URDF 파일 직접 수정]** 중 편한 방법을 선택해 진행할 수 있습니다.

---

#### 📌 센서 정의 기본 소스코드 (3D-LiDAR & Camera)

##### 1) 3D-LiDAR 센서 (Velodyne VLP-16 3D PointCloud)
* **설치 위치:** 차체 상단 (`base_link` 기준 Z: +0.35m, X: +0.1m)
* **발행 토픽:** `/points_raw` (`sensor_msgs/msg/PointCloud2`, Frame ID: `velodyne_link`)
* **Xacro / Gazebo 플러그인 코드:**
```xml
<!-- 3D-LiDAR Link & Joint -->
<link name="velodyne_link">
  <visual>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <geometry>
      <cylinder radius="0.05" length="0.07"/>
    </geometry>
    <material name="black">
      <color rgba="0.1 0.1 0.1 1.0"/>
    </material>
  </visual>
  <collision>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <geometry>
      <cylinder radius="0.05" length="0.07"/>
    </geometry>
  </collision>
  <inertial>
    <mass value="0.8"/>
    <origin xyz="0 0 0"/>
    <inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" iyz="0" izz="0.001"/>
  </inertial>
</link>

<joint name="velodyne_joint" type="fixed">
  <parent link="base_link"/>
  <child link="velodyne_link"/>
  <origin xyz="0.1 0 0.35" rpy="0 0 0"/>
</joint>

<!-- Gazebo 3D LiDAR Plugin -->
<gazebo reference="velodyne_link">
  <sensor type="ray" name="velodyne_sensor">
    <pose>0 0 0 0 0 0</pose>
    <visualize>false</visualize>
    <update_rate>10</update_rate>
    <ray>
      <scan>
        <horizontal>
          <samples>360</samples>
          <resolution>1</resolution>
          <min_angle>-3.14159265</min_angle>
          <max_angle>3.14159265</max_angle>
        </horizontal>
        <vertical>
          <samples>16</samples>
          <resolution>1</resolution>
          <min_angle>-0.261799</min_angle> <!-- -15 deg -->
          <max_angle>0.261799</max_angle>  <!-- +15 deg -->
        </vertical>
      </scan>
      <range>
        <min>0.3</min>
        <max>100.0</max>
        <resolution>0.001</resolution>
      </range>
    </ray>
    <plugin name="gazebo_ros_laser_controller" filename="libgazebo_ros_ray_sensor.so">
      <ros>
        <remapping>~/out:=/points_raw</remapping>
      </ros>
      <output_type>sensor_msgs/PointCloud2</output_type>
      <frame_name>velodyne_link</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

---

##### 2) Vision 카메라 센서 (RGB Camera)
* **설치 위치:** 차체 전방 (`base_link` 기준 Z: +0.25m, X: +0.45m)
* **발행 토픽:** `/camera/image_raw` (`sensor_msgs/msg/Image`, Frame ID: `camera_link`) 및 `/camera/camera_info`
* **Xacro / Gazebo 플러그인 코드:**
```xml
<!-- Camera Link & Joint -->
<link name="camera_link">
  <visual>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <geometry>
      <box size="0.03 0.08 0.03"/>
    </geometry>
    <material name="red">
      <color rgba="0.8 0.1 0.1 1.0"/>
    </material>
  </visual>
  <collision>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <geometry>
      <box size="0.03 0.08 0.03"/>
    </geometry>
  </collision>
  <inertial>
    <mass value="0.1"/>
    <origin xyz="0 0 0"/>
    <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/>
  </inertial>
</link>

<joint name="camera_joint" type="fixed">
  <parent link="base_link"/>
  <child link="camera_link"/>
  <origin xyz="0.45 0 0.25" rpy="0 0 0"/>
</joint>

<!-- Gazebo Camera Plugin -->
<gazebo reference="camera_link">
  <sensor type="camera" name="camera_sensor">
    <update_rate>30.0</update_rate>
    <camera name="front_camera">
      <horizontal_fov>1.3962634</horizontal_fov> <!-- 약 80도 -->
      <image>
        <width>640</width>
        <height>480</height>
        <format>R8G8B8</format>
      </image>
      <clip>
        <near>0.02</near>
        <far>300</far>
      </clip>
    </camera>
    <plugin name="camera_controller" filename="libgazebo_ros_camera.so">
      <ros>
        <remapping>~/image_raw:=/camera/image_raw</remapping>
        <remapping>~/camera_info:=/camera/camera_info</remapping>
      </ros>
      <camera_name>camera</camera_name>
      <frame_name>camera_link</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

---

#### 🛠️ 적용 방법 두 가지 설명

##### [방법 A] 신규 전용 파일 분리 (`sensors.xacro` 생성 - 추천 🌟)
1. `ros2_ws/src/hunter_robot/hunter_description/description/sensors.xacro` 파일 생성
2. 아래 내용 전체 저장:
```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
    <!-- 위에서 정의한 3D-LiDAR 코드 및 Camera 코드 전체를 여기에 넣습니다 -->
</robot>
```
3. `hunter_description/description/hunter.urdf.xacro`의 `<robot>` 태그 안쪽에 다음 include 구문 1줄 추가:
```xml
<xacro:include filename="$(find hunter_description)/description/sensors.xacro" />
```

##### [방법 B] 기존 파일 직접 수정 (`hunter_core.urdf.xacro` 수정)
1. `ros2_ws/src/hunter_robot/hunter_description/description/hunter_core.urdf.xacro` 파일 열기
2. `<xacro:macro name="dogbot" ...>` 태그 안쪽 맨 아래(휠 정의 바로 위) 또는 맨 끝에 위 **3D-LiDAR 코드 및 Camera 코드**를 직접 붙여넣기 후 저장.

---

### 3.3. [Step 2.3] RViz2 시각화 설정 프로파일 구축 (`view_hunter.rviz`)

3D-LiDAR(`PointCloud2`)와 카메라(`Image`) 데이터를 RViz2 화면에서 한눈에 모니터링할 수 있도록 시각화 항목을 추가하고 설정 프로파일(`view_hunter.rviz`)을 업데이트합니다.

#### 💡 적용 방법 2가지

##### [방법 1] RViz2 GUI 화면에서 버튼 클릭으로 추가 및 저장 (추천 🌟)
1. Gazebo 시뮬레이션 및 RViz2 구동:
   ```bash
   # ('ros2_ws/' 경로에서 실행)
   ros2 launch hunter_gazebo launch_sim.launch.py
   # (별도 터미널) 
   rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz
   ```
2. RViz2 프로그램 좌측 **Displays** 패널 하단의 **[Add]** 버튼 클릭
3. **[By topic]** 탭 선택 후 2개 항목 추가:
   * `/points_raw` 아래 **`PointCloud2`** 선택 → [OK]
   * `/camera/image_raw` 아래 **`Image`** 선택 → [OK]
4. **PointCloud2 옵션 조절**:
   * `Size (m)`: `0.03` (포인트 점 크기 조절)
   * `Color Transformer`: `Intensity` 또는 `AxisColor` (거리/강도별 무지개 색상 부여)
5. 설정 저장: 상단 메뉴 **File > Save Config** (단축키 `Ctrl + S`)를 눌러 `view_hunter.rviz` 파일에 반영

##### [방법 2] `view_hunter.rviz` 파일 직접 수정 (설정 코드 추가)
`ros2_ws/src/hunter_robot/hunter_gazebo/config/view_hunter.rviz` 파일의 `Displays:` 항목 아래에 아래 YAML 코드를 추가하고 저장합니다:

```yaml
    - Class: rviz_default_plugins/PointCloud2
      Enabled: true
      Name: PointCloud2
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /points_raw
      Size (m): 0.03
      Style: Points
      Value: true
    - Class: rviz_default_plugins/Image
      Enabled: true
      Name: CameraImage
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /camera/image_raw
      Value: true
```

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
