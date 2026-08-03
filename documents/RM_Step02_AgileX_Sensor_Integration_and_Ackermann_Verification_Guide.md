# RM Step 02: AgileX 차체 3D-LiDAR/카메라 센서 URDF 통합 및 아커만 조향 정밀 검증 가이드

본 문서는 **[프로젝트 개발 로드맵]**의 **2단계: AgileX 차체 3D-LiDAR/카메라 센서 URDF 통합 및 아커만 조향 정밀 검증 (`default.world`)**을 성공적으로 수행하기 위한 엔지니어링 상세 실행 가이드입니다.

---

## 1. 개요 및 목표

* **목표:** Gazebo 경량 기본 월드(`default.world`) 환경에서 AgileX Hunter 로봇의 URDF/Xacro 파일에 3D-LiDAR(Velodyne VLP-16 등) 센서와 RGB 카메라 링크 및 Gazebo ROS2 플러그인을 통합 장착하고, 아커만 전용 제어기 (`ackermann_steering_controller`)를 구축하여 RViz2에서 3D PointCloud, 실시간 카메라 영상 스트림 시각화와 정밀한 아커만 조향 동역학을 검증합니다.
* **주요 검증 요소:**
  - AgileX Hunter URDF/Xacro 모델에 3D-LiDAR 센서 및 Vision 카메라 링크/플러그인 추가 작성
  - `ackermann_controllers.yaml` 신규 생성을 통한 아커만 전용 컨트롤러 구축 및 전륜 조향 관절 연동
  - Gazebo 시뮬레이터 상에서 3D-LiDAR (`/points_raw`) 및 카메라 (`/camera/image_raw`) 토픽 수신 주기 모니터링
  - RViz2를 통한 3D 포인트 클라우드 및 실시간 카메라 영상 시각화
  - `teleop_twist_keyboard`를 이용해 곡선 주행 시 전륜 아커만 조향 각도(Steering Angle) 꺾임 궤적 및 오도메트리(`/odom`) 데이터 정밀도 검증

---

## 2. 사전 환경 및 의존성 패키지

- **OS:** Ubuntu 22.04 LTS (Jammy Jellyfish)
- **ROS 2:** Humble Hawksbill
- **시뮬레이터:** Gazebo Classic (v11) & RViz2
- **필수 ROS2 패키지:** `ros-humble-gazebo-plugins`, `ros-humble-velodyne-description`, `ros-humble-image-transport-plugins`, `ros-humble-rviz2`, `ros-humble-ackermann-steering-controller`, `ros-humble-ackermann-msgs`
- **대상 워크스페이스:** `~/Tae_ws/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws`

---

## 3. 단계별 상세 실행 절차

### 3.1. [Step 2.1] 센서 및 아커만 제어기 의존성 패키지 설치
터미널을 열고 3D-LiDAR, 카메라 및 아커만 조향 제어기 패키지를 설치합니다.

#### 📦 설치 대상 패키지 역할 및 설명
1. **`ros-humble-gazebo-plugins`**: Gazebo 가상 환경 내에서 센서(카메라, LiDAR, IMU 등)를 렌더링하고 시뮬레이션 데이터를 ROS 2 토픽으로 노출시켜 주는 공식 플러그인 모음입니다.
2. **`ros-humble-velodyne-description`**: 3D PointCloud 센서인 Velodyne LiDAR(VLP-16 등)의 3D 메쉬 파일 및 URDF 센서 링크 정의를 제공하는 패키지입니다.
3. **`ros-humble-image-transport-plugins`**: 카메라 영상 데이터(Raw Image)를 압축(JPEG/PNG, Compressed Depth 등)하여 네트워크 대역폭을 절약하고 전송할 수 있는 플러그인 모음입니다.
4. **`ros-humble-rviz2`**: ROS 2 환경에서 3D 센서 포인트클라우드, 로봇 3D 모델, TF 좌표계 및 2D/3D 지도를 실시간으로 관찰할 수 있는 표준 시각화 도구입니다.
5. **`ros-humble-ackermann-steering-controller`**: 전륜 조향 및 후륜 구동 구조인 AgileX Hunter 차량 전용 **아커만 조향 제어기 플러그인**입니다.
6. **`ros-humble-ackermann-msgs`**: 아커만 조향 제어에 필요한 속도 및 조향각 데이터 규격(`ackermann_msgs/msg/AckermannDrive`)을 정의하는 전용 메시지 패키지입니다.
7. **`ros-humble-steering-controllers-library`**: 조향 기반 차량 제어기(Ackermann, Tricycle 등)의 공통 역동학 계산 및 궤적 수송을 다루는 하위 C++ 라이브러리입니다.

```bash
sudo apt update
sudo apt install -y \
  ros-humble-gazebo-plugins \
  ros-humble-velodyne-description \
  ros-humble-image-transport-plugins \
  ros-humble-rviz2 \
  ros-humble-ackermann-steering-controller \
  ros-humble-ackermann-msgs \
  ros-humble-steering-controllers-library
```

---

### 3.2. [Step 2.2] Hunter URDF/Xacro 파일에 3D-LiDAR 및 카메라 센서 정의 추가

#### 📌 센서 정의 기본 소스코드 (3D-LiDAR & Camera)

##### 1) 3D-LiDAR 센서 (Velodyne VLP-16 3D PointCloud)
* **설치 위치:** 차체 상단 (`base_link` 기준 Z: +0.35m, X: +0.1m)
* **발행 토픽:** `/points_raw` (`sensor_msgs/msg/PointCloud2`, Frame ID: `velodyne_link`)
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
          <min_angle>-0.261799</min_angle>
          <max_angle>0.261799</max_angle>
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

##### 2) Vision 카메라 센서 (RGB Camera)
* **설치 위치:** 차체 전방 (`base_link` 기준 Z: +0.25m, X: +0.45m)
* **발행 토픽:** `/camera/image_raw` (`sensor_msgs/msg/Image`, Frame ID: `camera_link`) 및 `/camera/camera_info`
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
      <horizontal_fov>1.3962634</horizontal_fov>
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

* **적용 파일 위치:** `ros2_ws/src/hunter_robot/hunter_description/description/sensors.xacro` 신규 생성 및 `hunter.urdf.xacro`에 include 추가.

---

### 3.3. [Step 2.3] 아커만 전용 컨트롤러 구축 (`ackermann_controllers.yaml`) 🌟

기존 원본 `controllers.yaml`은 유지하고, Hunter 2.0 물리 제원(축거 `0.512m`, 윤거 `0.4908m`, 바퀴 반지름 `0.09906m`)을 정확히 반영하는 신규 아커만 제어 파라미터를 구축합니다.

#### 1) `ackermann_controllers.yaml` 신규 작성
* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/ackermann_controllers.yaml`

```yaml
controller_manager:
  ros__parameters:
    update_rate: 50
    use_sim_time: true

    ackermann_steering_controller:
      type: ackermann_steering_controller/AckermannSteeringController

    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster

ackermann_steering_controller:
  ros__parameters:
    # ⚠️ 주의: ROS 2 ackermann_steering_controller는 배열의 [0]을 우측, [1]을 좌측으로 내부 매핑합니다.
    # 반드시 [Right, Left] 순서로 기입해야 기하학이 깨지지 않고 부드럽게 조향됩니다.
    rear_wheels_names: ["back_right_wheel_joint", "back_left_wheel_joint"]
    front_wheels_names: ["front_right_steering_joint", "front_left_steering_joint"]

    wheelbase: 0.512                  # 축거 (전륜-후륜 중심 거리 실측값)
    front_wheel_track: 0.4908          # 전륜 윤거 (좌-우 바퀴 거리 실측값)
    rear_wheel_track: 0.4908           # 후륜 윤거 (좌-우 바퀴 거리 실측값)
    front_wheels_radius: 0.09906      # 바퀴 반지름 (0.1651 * 0.6 실측값)
    rear_wheels_radius: 0.09906       # 바퀴 반지름 (0.1651 * 0.6 실측값)

    odom_frame_id: odom
    base_frame_id: base_link
    enable_odom_tf: true             # 👈 odom -> base_link TF 필수 발행

    publish_rate: 50.0
    open_loop: true                  # 🌟 물리엔진 바퀴 슬립 무시, cmd_vel로 오도메트리 계산
    use_stamped_vel: false
    cmd_vel_timeout: 1.0             # 키보드 신호 끊김 방지 타임아웃

    linear.x.has_velocity_limits: true
    linear.x.max_velocity: 1.5
    linear.x.min_velocity: -1.0
    linear.x.has_acceleration_limits: true
    linear.x.max_acceleration: 1.0

    angular.z.has_velocity_limits: true
    angular.z.max_velocity: 1.0      # 허용 조향 각도 (1.0 rad)
    angular.z.has_acceleration_limits: true
    angular.z.max_acceleration: 1.0

# 🌟 물리엔진 조향축 고정용 강력한 PID 게인 추가
gazebo_ros2_control:
  ros__parameters:
    pid_gains:
      front_left_steering_joint: {p: 100.0, i: 0.0, d: 1.0}
      front_right_steering_joint: {p: 100.0, i: 0.0, d: 1.0}
      back_left_wheel_joint: {p: 100.0, i: 0.0, d: 1.0}
      back_right_wheel_joint: {p: 100.0, i: 0.0, d: 1.0}
```

#### 2) `ros2_control.xacro` 전륜 조향 관절 등록 및 yaml 지정
* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_description/description/ros2_control.xacro`

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">

    <ros2_control name="GazeboSystem" type="system">
        <hardware>
            <plugin>gazebo_ros2_control/GazeboSystem</plugin>
        </hardware>

        <joint name="front_left_steering_joint">
            <command_interface name="position"/>
            <state_interface name="position"/>
        </joint>
        
        <joint name="front_right_steering_joint">
            <command_interface name="position"/>
            <state_interface name="position"/>
        </joint>

        <!-- 🌟 앞바퀴(전륜) 수동 관절(Passive) 추가: RViz2 시각화용 -->
        <joint name="front_right_wheel_joint">
            <!-- <command_interface name="velocity">
                <param name="min">-10</param>
                <param name="max">10</param>
            </command_interface> -->
            <state_interface name="velocity"/>
            <state_interface name="position"/>
        </joint>
        
        <joint name="front_left_wheel_joint">
            <!-- <command_interface name="velocity">
                <param name="min">-10</param>
                <param name="max">10</param>
            </command_interface> -->
            <state_interface name="velocity"/>
            <state_interface name="position"/>
        </joint>

        <joint name="back_right_wheel_joint">
            <command_interface name="velocity">
                <param name="min">-10</param>
                <param name="max">10</param>
            </command_interface>
            <state_interface name="velocity"/>
            <state_interface name="position"/>
        </joint>
        
        <joint name="back_left_wheel_joint">
            <command_interface name="velocity">
                <param name="min">-10</param>
                <param name="max">10</param>
            </command_interface>
            <state_interface name="velocity"/>
            <state_interface name="position"/>
        </joint>
    </ros2_control>

    <gazebo>
        <plugin name="gazebo_ros2_control_hunter" filename="libgazebo_ros2_control.so">
            <parameters>$(find hunter_gazebo)/config/ackermann_controllers.yaml</parameters>
            <ros>
                <remapping>/ackermann_steering_controller/reference_unstamped:=/cmd_vel</remapping>
                <remapping>/ackermann_steering_controller/tf_odometry:=/tf</remapping>
            </ros>
        </plugin>
    </gazebo>

</robot>
```

#### 3) `launch_sim.launch.py` 아커만 스포너 적용
* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/launch_sim.launch.py`

```python
    ackermann_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["ackermann_steering_controller"],
    )

    return LaunchDescription([
        rsp,
        gazebo,
        spawn_entity,
        ackermann_spawner,
        joint_broad_spawner
        # joint_state_publisher  # 🌟 더미 퍼블리셔 제거: TF 충돌(깜빡임) 예방
    ])
```

#### 4) `wheel.urdf.xacro` 전륜 Z축 조향 관절 및 마찰력 보정 🌟
* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_description/description/wheel.urdf.xacro`
* **수정 내용**: 전륜 조향 매크로(`hunter_steering_wheel`) 추가, 조향 관절 한계값(`limit lower="-1.2" upper="1.2"`), 감쇄(`damping="1.0"`), 마찰축(`fdir1`) 제거 및 마찰력(`0.5`) 적용.

```xml
  <xacro:macro name="hunter_steering_wheel" params="wheel_prefix x y z roll:=0.0 pitch:=0.0 yaw:=0.0 is_sim:=true">
    <link name="${wheel_prefix}_steering_link">
      <inertial>
        <mass value="0.5" />
        <origin xyz="0 0 0" />
        <inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" iyz="0" izz="0.001" />
      </inertial>
    </link>
    <joint name="${wheel_prefix}_steering_joint" type="revolute">
      <parent link="base_link"/>
      <child link="${wheel_prefix}_steering_link"/>
      <origin xyz="${x} ${y} ${z}" rpy="${roll} ${pitch} ${yaw}"/>
      <axis xyz="0 0 1"/>
      <limit lower="-1.2" upper="1.2" effort="100.0" velocity="2.0"/>
      <dynamics damping="1.0" friction="0.1"/>
    </joint>
    <link name="${wheel_prefix}_wheel">
      <inertial>
        <mass value="2.637" />
        <origin xyz="0 0 0" />
        <inertia ixx="0.02467" ixy="0" ixz="0" iyy="0.04411" iyz="0" izz="0.02467" />
      </inertial>
      <visual>
        <origin xyz="0 0 0" rpy="0 0 0" />
        <geometry>
          <mesh filename="file://$(find hunter_description)/meshes/wheel.dae" scale="0.6 0.6 0.6"/>
        </geometry>
      </visual>
      <collision>
        <origin xyz="0 0 0" rpy="${M_PI/2} 0 0" />
        <geometry>
          <cylinder length="${wheel_length * 0.6}" radius="${wheel_radius * 0.6}" />
        </geometry>
      </collision>
    </link>
    <joint name="${wheel_prefix}_wheel_joint" type="continuous">
      <parent link="${wheel_prefix}_steering_link"/>
      <child link="${wheel_prefix}_wheel"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <axis xyz="0 1 0"/>
    </joint>
    <gazebo reference="${wheel_prefix}_wheel">
      <mu1 value="100.0"/>
      <mu2 value="100.0"/>
      <kp value="10000000.0" />
      <kd value="1.0" />
    </gazebo>
  </xacro:macro>
```

#### 5) `hunter_core.urdf.xacro` 조향 바퀴 매크로 적용 및 지면 오프셋 보정 🌟
* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_description/description/hunter_core.urdf.xacro`
* **수정 내용**: 56번째 줄 `base_footprint_joint` 오프셋(`${wheel_vertical_offset - wheel_radius * 0.6}`) 정밀 지면 착지 보정 및 전륜 바퀴 2개에 `hunter_steering_wheel` 적용.

```xml
    <joint name="${prefix}base_footprint_joint" type="fixed">
      <origin xyz="0 0 ${wheel_vertical_offset - wheel_radius * 0.6}" rpy="0 0 0" />
      <parent link="${prefix}base_link" />
      <child link="${prefix}base_footprint" />
    </joint>
...
    <xacro:hunter_steering_wheel wheel_prefix="${prefix}front_left" x="${wheelbase/2}" y="${track/2}" z="${wheel_vertical_offset}" is_sim="${is_sim}"/>
    <xacro:hunter_steering_wheel wheel_prefix="${prefix}front_right" x="${wheelbase/2}" y="${-track/2}" z="${wheel_vertical_offset}" is_sim="${is_sim}"/>
    <xacro:hunter_wheel wheel_prefix="${prefix}back_left" x="${-wheelbase/2}" y="${track/2}" z="${wheel_vertical_offset}" is_sim="${is_sim}"/>
    <xacro:hunter_wheel wheel_prefix="${prefix}back_right" x="${-wheelbase/2}" y="${-track/2}" z="${wheel_vertical_offset}" is_sim="${is_sim}"/>
```

#### 6) `rsp.launch.py` Gazebo 파싱 버그 예방 코드 추가 🌟
* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_description/launch/rsp.launch.py`
* **수정 내용**: 24번째 줄 `node_robot_state_publisher` 전달 전 `robot_description` XML 주석 내 `--` 문제로 인한 `gazebo_ros2_control` rcl 파서 에러 예방 로직 추가.

```python
    # Create a robot_state_publisher node
    doc_xml = robot_description_config.toxml()
    import re
    doc_xml = re.sub(r'<!--.*?-->', '', doc_xml, flags=re.DOTALL)
    params = {'robot_description': doc_xml, 'use_sim_time': use_sim_time}
```

---

### 3.4. [Step 2.4] RViz2 시각화 프로파일 구축 및 모니터링 (`view_hunter.rviz`)

1. Gazebo 시뮬레이션 및 RViz2 구동:
   ```bash
   colcon build --symlink-install
   source install/setup.bash
   ros2 launch hunter_gazebo launch_sim.launch.py
   # (별도 터미널) 
   rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz
   ```
2. RViz2 프로그램 패널에서 `/points_raw` (`PointCloud2`) 및 `/camera/image_raw` (`Image`) 항목 추가.

---

### 3.5. [Step 2.5] 키보드 텔레옵 조종 및 아커만 조향 동역학 검증

```bash
# 1. 키보드 제어 노드 구동
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 2. 오도메트리 토픽 모니터링
ros2 topic echo /odom
```
* Gazebo 상에서 전륜 바퀴가 실제로 꺾이며 곡선 주행하고, `/odom` 궤적 정보가 회전각과 100% 일치하며 정밀 수신되는지 확인합니다.

---

## 4. 검증 체크리스트 (Verification Checklist)

| 번호 | 검증 항목 | 검증 방법 및 기준 | 통과 여부 |
|:---:|:---|:---|:---:|
| 1 | **3D-LiDAR 스폰 & 토픽** | Gazebo 차체 상단에 3D-LiDAR 모델이 정상 표시되고 `/points_raw` 토픽이 10Hz 이상 발행됨 | [ ] |
| 2 | **카메라 스폰 & 토픽** | Gazebo 차체 전방에 카메라 모델이 정상 표시되고 `/camera/image_raw` 토픽이 20~30Hz 발행됨 | [ ] |
| 3 | **아커만 스포너 & TF** | `ackermann_steering_controller`가 스폰되고 `odom` -> `base_link` TF가 50Hz로 정상 발행됨 | [ ] |
| 4 | **아커만 조향 동역학** | 키보드 회전 조종 시 전륜 조향각이 실시간 꺾이고 `/odom` 궤적이 회전각과 왜곡 없이 일치함 | [ ] |

---

## 5. 트러블슈팅 (Troubleshooting & Known Issues)

* **문제 1: `ackermann_steering_controller` 스폰 시 `Resource not found` 에러가 발생하는 경우**
  - **원인:** ROS2 Humble 아커만 패키지가 설치되지 않음.
  - **해결:** `sudo apt install ros-humble-ackermann-steering-controller ros-humble-ackermann-msgs` 설치 후 재실행.

* **문제 2: 아커만 조향 시 차체가 회전하지 않는 경우**
  - **원인:** `ros2_control.xacro` 파일 내 전륜 조향 관절(`front_left_steering_joint`, `front_right_steering_joint`)의 position 인터페이스 선언 누락.
  - **해결:** `ros2_control.xacro`에 전륜 관절 position command_interface 등록 확인.

* **문제 3: 조향 시 타이어 방향은 맞는데 차체가 반대로 회전하거나, 회전 시 바퀴가 끌리며 덜컹거리는 경우**
  - **증상:** `teleop` 조종 시 직진 좌/우회전 방향이 반대로 먹거나, 회전 자체는 되지만 몹시 부자연스럽고 슬립이 발생함.
  - **원인:** `ackermann_controllers.yaml`의 바퀴 배열 순서 오류. `ackermann_steering_controller`는 내부적으로 배열의 첫 번째 인덱스(`[0]`)를 **우측(Right) 바퀴**, 두 번째 인덱스(`[1]`)를 **좌측(Left) 바퀴**로 인식합니다. 만약 흔히 생각하는 `[Left, Right]` 순서로 기재할 경우, 내륜/외륜의 조향 각도와 속도 제어가 좌우 반대로 들어가 아커만 기하학이 붕괴됩니다.
  - **해결:** 
    1. `ackermann_controllers.yaml`에서 `front_wheels_names`와 `rear_wheels_names` 모두 `[우측 관절, 좌측 관절]` 순서로 배치합니다.
    2. `wheel.urdf.xacro`의 조향 관절 축이 표준 반시계방향(CCW) 회전인 `<axis xyz="0 0 1"/>`로 되어 있는지 확인합니다.
