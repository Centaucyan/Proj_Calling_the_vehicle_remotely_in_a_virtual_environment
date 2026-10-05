# [포트폴리오] Gazebo 3D 환경에서 아커만 동역학 모델링과 3D-LiDAR 필터링을 통한 SLAM 왜곡 해결 및 Nav2 자율주행 파이프라인 구축

> **부제:** 테슬라 Smart Summon 구현을 위한 가상 주차장 아커만 모빌리티 자율주행 시스템 개발  
> **프로젝트 기간:** 2026.07.15 ~ 2026.08.20 (전체 10단계 로드맵 중 5단계 자율주행 프레임워크 구축 완료)  
> **역할 및 기여도:** 개인 프로젝트 (로봇 섀시 동역학 모델링, 센서 통합, SLAM 지도 작성, Nav2 파라미터 튜닝 및 트러블슈팅 100% 단독 수행)  
> **Github Repository:** [Centaucyan/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment](https://github.com/Centaucyan/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment.git)

---

## 1. Overview (프로젝트 개요 및 핵심 요약)

### 1.1. 프로젝트 배경 및 목표
* **목표:** 테슬라의 **Smart Summon(원격 차량 호출)** 기능을 Gazebo 3D 가상 환경에서 구현하는 것을 목표로 함.
* **핵심 과제:** 일반적인 차동 구동(Differential Drive) 방식과 달리 제자리 회전이 불가능한 **아커만 조향(Ackermann Steering) 차량(AgileX Hunter 2.0)**의 물리적 한계를 극복하고, 가상 주차장 환경에서 장애물을 회피하며 목적지까지 부드럽고 안전하게 자율주행하는 전 파이프라인을 완성함.

### 1.2. 핵심 성과 (Key Achievements)
* **섀시 동역학 재설계:** 기존 오픈소스의 가짜 4륜 차동 구동 설정을 폐기하고, 실제 차량 규격(축거 `0.512m`, 윤거 `0.4908m`)을 반영하여 전륜 조향(Revolute Joint)-후륜 구동(Continuous Joint)의 물리적 아커만 조향 모델을 URDF에 직접 설계.
* **3D-LiDAR 지면 반사 노이즈 필터링:** 16채널 3D-LiDAR(Velodyne VLP-16) 하향 빔으로 인한 SLAM 지도 회전/왜곡 문제를 데이터 분석으로 규명하고, 기하학적 높이 슬라이싱(`-0.1m ~ 1.0m`)을 통해 오차 없는 2D 점유 격자 지도(`0.05m/cell`) 구축.
* **아커만 특화 Nav2 자율주행 파이프라인 완성:**
  * **전역 플래너:** 차동 구동용 `NavfnPlanner (A*)`의 직각 경로 한계를 극복하기 위해, 최소 회전 반경($1.6\text{m}$)과 전후진(K-turn)을 지원하는 **`SmacPlannerHybrid (Hybrid-A*)` with `REEDS_SHEPP`** 모션 모델 적용.
  * **지역 제어기:** 제자리 회전 명령을 원천 차단하고 후진 주행을 허용하는 **`RegulatedPurePursuitController (RPP)`** 최적 튜닝.
  * **복구 동작:** 비홀로노믹 차량에서 불가능한 `Spin`(제자리 회전) 플러그인을 제거하고 `BackUp`과 `DriveOnHeading`으로 재구성.

---

## 2. System Architecture & Tech Stack (시스템 구조 및 기술 스택)

### 2.1. 기술 스택 (Tech Stack)
* **OS:** `Ubuntu 22.04 LTS (Jammy Jellyfish)`
* **Middleware:** `ROS 2 Humble Hawksbill` (C++, Python 3.10)
* **Simulator:** `Gazebo Classic (v11)`, `RViz2`
* **Control & Dynamics:** `ros2_control`, `ackermann_steering_controller`, `gazebo_ros2_control`
* **Sensors:** `Velodyne VLP-16 (16ch 3D-LiDAR)`, `RGB Camera`
* **SLAM & Navigation:** `slam_toolbox` (Ceres Solver), `pointcloud_to_laserscan`, `Navigation2 (Nav2)`

### 2.2. 계층형 시스템 아키텍처 (5-Layer Architecture)
1. **User Interface 계층:** Qt 기반 통합 대시보드 (가상 리모컨 호출 버튼 및 차량 상태 모니터링)
2. **Middleware 계층:** ROS 2 Humble (노드 라이프사이클 관리, 토픽/액션 비동기 통신)
3. **AI & Algorithm 계층:** 
   * 2D 점유 격자 지도 작성 (`slam_toolbox`)
   * 전역/지역 경로 계획 (`SmacPlannerHybrid`, `RegulatedPurePursuitController`)
   * 위치 추정 (`AMCL`) 및 동적/정적 장애물 비용 지도 (`Costmap 2D`)
4. **Simulation 계층:** Gazebo 3D 가상 주차장 월드 (`parking_garage.world`) 및 AgileX Hunter 2.0 모델
5. **OS 계층:** Ubuntu 22.04 LTS

### 2.3. ROS 2 데이터 흐름도 (Data Flow Diagram)
```
[Gazebo 3D World] 
   │ (센서 데이터 발행 & 물리 제어)
   ├─► /points_raw (sensor_msgs/PointCloud2) ──► [pointcloud_to_laserscan] ──► /scan (LaserScan)
   │                                                                               │
   ├─► /camera/image_raw (sensor_msgs/Image)                                       ├─► [slam_toolbox] ──► /map
   ├─► /odom (nav_msgs/Odometry) ──────────────────────────────────────────────────┼─► [AMCL / Costmaps]
   │                                                                               ▼
   │                                                                        [Nav2 Stack]
   │                                                                        ├─ Planner: Smac Hybrid-A*
   │                                                                        └─ Controller: RPP
   │                                                                               │
   └◄─ /cmd_vel (geometry_msgs/Twist) ◄── [ackermann_steering_controller] ◄──────┘
```

---

## 3. 핵심 기술 구현 및 시스템 엔지니어링 (Core Engineering)

### 3.1. AgileX Hunter 섀시 URDF 모델링 및 아커만 조향 인터페이스 설계
* **개요:** 기존 오픈소스의 차동 구동(Diff-drive) 방식을 폐기하고, 실제 차량 규격을 1:1 반영하여 전륜 조향(Revolute Joint)-후륜 구동(Continuous Joint)의 물리적 아커만 조향 모델을 직접 설계함.

#### 📊 실측 제원 vs URDF/ROS 2 파라미터 매핑
| 제원 항목 | 실측 규격 | 정의 파일 | 파라미터 / 태그 | 적용값 |
| :--- | :--- | :--- | :--- | :--- |
| **축거 (Wheelbase)** | 전륜-후륜 중심 거리 | `ackermann_controllers.yaml` | `wheelbase` | **`0.512 m`** |
| **윤거 (Track)** | 좌우 바퀴 중심 거리 | `ackermann_controllers.yaml` | `front/rear_wheel_track` | **`0.4908 m`** |
| **바퀴 반지름 (Radius)** | 타이어 반지름 ($0.1651 \times 0.6$) | `ackermann_controllers.yaml` | `front/rear_wheels_radius` | **`0.09906 m`** |
| **최대 조향각 한계** | 전륜 킹핀 회전 가동 범위 | `wheel.urdf.xacro` | `<limit lower="..." upper="..."/>` | **$\pm 1.2 \text{ rad}$ ($\approx \pm 68.7^\circ$)** |
| **최대 선속도 (Speed)** | 차량 전진 / 후진 한계 속도 | `ackermann_controllers.yaml` | `linear.x.max/min_velocity` | **`1.5 m/s / -1.0 m/s`** |
| **최대 각속도 (Angular)**| 조향 회전 각속도 한계 | `ackermann_controllers.yaml` | `angular.z.max_velocity` | **`1.0 rad/s`** |

#### 💻 전륜 조향 관절 설계 코드 (`wheel.urdf.xacro`)
```xml
<!-- 전륜 조향 전용 매크로: Z축 Revolute Joint 추가 -->
<xacro:macro name="hunter_steering_wheel" params="wheel_prefix x y z roll:=0.0 pitch:=0.0 yaw:=0.0 is_sim:=true">
  <link name="${wheel_prefix}_steering_link">
    <inertial>
      <mass value="0.5" />
      <origin xyz="0 0 0" />
      <inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" izz="0.001" />
    </inertial>
  </link>

  <!-- 🌟 Z축 회전(조향각)을 담당하는 Revolute 관절 정의 -->
  <joint name="${wheel_prefix}_steering_joint" type="revolute">
    <parent link="base_link"/>
    <child link="${wheel_prefix}_steering_link"/>
    <origin xyz="${x} ${y} ${z}" rpy="${roll} ${pitch} ${yaw}"/>
    <axis xyz="0 0 1"/> <!-- Z축 회전축 -->
    <limit lower="-1.2" upper="1.2" effort="100.0" velocity="2.0"/>
    <dynamics damping="1.0" friction="0.1"/>
  </joint>

  <!-- 조향 너클 하부에 결합되어 회전하는 구동 휠 (Y축 회전) -->
  <joint name="${wheel_prefix}_wheel_joint" type="continuous">
    <parent link="${wheel_prefix}_steering_link"/>
    <child link="${wheel_prefix}_wheel"/>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
  </joint>
</xacro:macro>
```

#### 💻 ros2_control 하드웨어 인터페이스 바인딩 (`ros2_control.xacro`)
```xml
<ros2_control name="GazeboSystem" type="system">
    <hardware>
        <plugin>gazebo_ros2_control/GazeboSystem</plugin>
    </hardware>
    <!-- 전륜: Position(조향각) 제어 인터페이스 -->
    <joint name="front_left_steering_joint">
        <command_interface name="position"/><state_interface name="position"/>
    </joint>
    <joint name="front_right_steering_joint">
        <command_interface name="position"/><state_interface name="position"/>
    </joint>
    <!-- 후륜: Velocity(구동속도) 제어 인터페이스 -->
    <joint name="back_right_wheel_joint">
        <command_interface name="velocity"/><state_interface name="velocity"/><state_interface name="position"/>
    </joint>
    <joint name="back_left_wheel_joint">
        <command_interface name="velocity"/><state_interface name="velocity"/><state_interface name="position"/>
    </joint>
</ros2_control>
```

---

### 3.2. 가상 주차장 월드 모델링 및 3D 센서 가상화
* **개요:** 차량 규격에 맞춘 가상 주차장 월드(`parking_garage.world`)를 직접 SDF로 모델링하고, 순정 빈 섀시 모델에 **16채널 3D-LiDAR(Velodyne VLP-16)**와 **전방 RGB 카메라**를 차체 URDF 링크에 기구학적으로 장착 및 가상화함.

#### 📡 장착 센서 사양 및 차체 결합 좌표 (TF Offset)
| 센서 명칭 | 모델 및 스펙 | 기준 링크 (Parent) | 결합 위치 오프셋 (`xyz`) | 발행 토픽 / 프레임 | 목적 및 역할 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **3D-LiDAR** | **Velodyne VLP-16 Puck**<br>(16채널, 수직 $\pm 15^\circ$, 10 Hz) | `base_link` | **`0.1 0 0.35`**<br>(전방 10cm, 높이 35cm 상단) | `/points_raw`<br>(`velodyne_link`) | 3D 점군 스캔 ➡️ 2D LaserScan 변환 후 SLAM 및 Costmap 장애물 감지 |
| **전방 카메라** | **RGB Camera**<br>(640×480, 30 FPS, FOV $80^\circ$) | `base_link` | **`0.35 0 0.25`**<br>(최전방 35cm, 높이 25cm 범퍼) | `/camera/image_raw`<br>(`camera_link`) | 향후 Vision AI 기반 주차 기둥/벽면 감지 및 정밀 주차 영상 인식 |

#### 💻 16채널 3D-LiDAR (Velodyne VLP-16) 장착 코드 (`sensors.xacro`)
```xml
<link name="velodyne_link">
  <visual><geometry><cylinder radius="0.05" length="0.07"/></geometry><material name="black"/></visual>
  <collision><geometry><cylinder radius="0.05" length="0.07"/></geometry></collision>
  <inertial><mass value="0.8"/><inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" izz="0.001"/></inertial>
</link>

<!-- 🌟 차체 상단 고정 Fixed Joint (X: +0.1m, Z: +0.35m) -->
<joint name="velodyne_joint" type="fixed">
  <parent link="base_link"/>
  <child link="velodyne_link"/>
  <origin xyz="0.1 0 0.35" rpy="0 0 0"/>
</joint>

<gazebo reference="velodyne_link">
  <sensor type="ray" name="velodyne_sensor">
    <update_rate>10</update_rate>
    <ray>
      <scan>
        <horizontal><samples>360</samples><min_angle>-3.14159</min_angle><max_angle>3.14159</max_angle></horizontal>
        <vertical><samples>16</samples><min_angle>-0.2618</min_angle><max_angle>0.2618</max_angle></vertical>
      </scan>
      <range><min>0.3</min><max>100.0</max><resolution>0.001</resolution></range>
    </ray>
    <plugin name="gazebo_ros_laser_controller" filename="libgazebo_ros_ray_sensor.so">
      <ros><remapping>~/out:=/points_raw</remapping></ros>
      <output_type>sensor_msgs/PointCloud2</output_type>
      <frame_name>velodyne_link</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

#### 💻 전방 RGB 카메라 장착 코드 (`sensors.xacro`)
```xml
<link name="camera_link">
  <visual><geometry><box size="0.03 0.08 0.03"/></geometry><material name="red"/></visual>
  <collision><geometry><box size="0.03 0.08 0.03"/></geometry></collision>
  <inertial><mass value="0.1"/><inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" izz="0.0001"/></inertial>
</link>

<!-- 🌟 차체 전방 범퍼 상단 결합 Fixed Joint (X: +0.35m, Z: +0.25m) -->
<joint name="camera_joint" type="fixed">
  <parent link="base_link"/>
  <child link="camera_link"/>
  <origin xyz="0.35 0 0.25" rpy="0 0 0"/>
</joint>

<gazebo reference="camera_link">
  <sensor type="camera" name="camera_sensor">
    <update_rate>30.0</update_rate>
    <camera name="front_camera">
      <horizontal_fov>1.3962634</horizontal_fov>
      <image><width>640</width><height>480</height><format>R8G8B8</format></image>
      <clip><near>0.02</near><far>300</far></clip>
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

#### 💻 최상위 로봇 모델에 센서 Xacro 모듈화 결합 (`hunter.urdf.xacro`)
```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="robot">
    <!-- 🌟 센서 모듈 include 결합 -->
    <xacro:include filename="$(find hunter_description)/description/sensors.xacro" />
    <xacro:include filename="$(find hunter_description)/description/hunter_core.urdf.xacro"/>
    <xacro:dogbot prefix="$(arg prefix)" is_sim="$(arg is_sim)"/>
    <xacro:if value="$(arg use_ros2_control)">
        <xacro:include filename="$(find hunter_description)/description/ros2_control.xacro" />
    </xacro:if>
</robot>
```

---

### 3.3. 통합 자율주행 브링업 파이프라인 구축 (`bringup_sim_nav2.launch.py`)
시뮬레이터 구동부터 센서 변환, Nav2 스택 활성화까지 단 한 번의 명령어로 전체 시스템이 유기적으로 기동되도록 계층적 런치 구조 설계.

```
bringup_sim_nav2.launch.py
 ├── 1. launch_sim.launch.py (Gazebo 월드 로드 + 로봇 스폰 + ros2_control 구동)
 ├── 2. pointcloud_to_laserscan_node (3D PointCloud ➡️ 2D LaserScan 실시간 투영 변환)
 └── 3. navigation.launch.py (Map Server, AMCL, Planner, Controller, BT Navigator 기동)
```

---

## 4. 실전 심층 트러블슈팅 (Deep-dive Troubleshooting) 🌟

### 📌 Case 1. [센서/SLAM] 3D-LiDAR 지면 반사 및 조향축 슬립으로 인한 SLAM 지도 왜곡 규명
* **문제 현상:** `slam_toolbox`로 지도 작성 중 지도가 시계방향으로 계속 삐뚤어지며 회전하고, 전진할 때 실제 외벽이 로봇 쪽으로 다가오는 스케일 왜곡(Map Drift) 발생.
* **근본 원인 분석:**
  1. **바닥면을 벽으로 오인:** 16채널 3D-LiDAR 중 하향 빔이 바닥을 때리면서 생긴 동심원 궤적이 로봇을 항상 따라다님. SLAM 알고리즘이 바닥을 벽으로 착각하여, 로봇의 실제 전진 거리(1m)를 0.2m만 움직였다고 오판(스캔 매칭 실패).
  2. **조향축 물리 슬립 & 더미 노드 충돌:** Gazebo 물리 하중으로 앞바퀴가 0도를 유지하지 못하고 미세하게 틀어짐 + 더미 `joint_state_publisher`가 강제로 "조향각은 0도"라고 덮어씌워 TF 좌표계 충돌 발생.
* **해결 방안 및 조치:**
  * `pointcloud_to_laserscan` 노드의 높이 슬라이싱 파라미터를 수정하여 지면 레이저를 100% 필터링.
  * 조향 관절에 강력한 PID 게인을 부여해 조향축을 고정하고 더미 노드 비활성화.

#### 💻 [Before ❌ vs After ⭕ 코드 비교]
```yaml
# 1) mapper_params_online_async.yaml (지면 레이저 필터링)
pointcloud_to_laserscan:
  ros__parameters:
    # ❌ Before: 바닥면(Z=0)까지 포함되어 지면 궤적이 가짜 장애물로 스캔됨
    # min_height: -0.3

    # ⭕ After: LiDAR 장착 높이(0.35m) 기준 바닥면을 완전히 배제하고 벽체만 슬라이싱
    min_height: -0.1
    max_height: 1.0

# 2) ackermann_controllers.yaml (조향축 PID 고정)
# ❌ Before: PID 게인이 없어 차체 하중에 의해 바퀴가 0도에서 미끄러짐 (설정 없음)

# ⭕ After: 물리엔진 조향축 고정용 강력한 PID 게인 투입
gazebo_ros2_control:
  ros__parameters:
    pid_gains:
      front_left_steering_joint: {p: 100.0, i: 0.0, d: 1.0}
      front_right_steering_joint: {p: 100.0, i: 0.0, d: 1.0}
```
* **성과:** 지면 노이즈가 완벽히 제거되어 외벽과 4개 직각 기둥이 왜곡 없이 일치하는 정방형 2D 격자 지도 획득 (`parking_garage_map.pgm`).

---

### 📌 Case 2. [아키텍처/Lifecycle] Gazebo-Nav2 전역 런치 파라미터 충돌 및 Lifecycle 에러 해결
* **문제 현상:** 통합 런치 실행 시 RViz2 화면에 지도가 전혀 뜨지 않고 `No map received`, `Fixed Frame [map] does not exist` 에러 발생.
* **근본 원인 분석:**
  1. **Behavior Server 누락:** ROS 2 Humble의 `bt_navigator`는 복구 동작을 위해 `behavior_server` 노드를 필수로 요구하나 설정에서 누락됨 ➡️ 라이프사이클 매니저가 안전을 위해 전체 노드를 연쇄 비활성화(Deactivate)함.
  2. **전역 런치 변수명 충돌:** Gazebo 내부 런치와 `navigation.launch.py`가 모두 `params_file`이라는 동일한 변수명을 사용하여, Gazebo의 빈 문자열(`''`)이 Nav2 파라미터를 덮어씌움 ➡️ Nav2 노드들이 파라미터를 읽지 못해 다운됨.
* **해결 방안 및 조치:**
  * `navigation.launch.py`의 변수명을 변경하여 네임스페이스를 분리하고 `behavior_server` 라이프사이클 등록.

#### 💻 [Before ❌ vs After ⭕ 코드 비교]
```python
# navigation.launch.py

# ❌ Before: Gazebo의 빈 변수와 충돌하여 nav2_params.yaml이 증발함
# declare_params_file_cmd = DeclareLaunchArgument('params_file', ...)

# ⭕ After: 고유한 변수명으로 변경하여 전역 충돌 원천 차단
declare_nav_params_file_cmd = DeclareLaunchArgument(
    'nav_params_file',
    default_value=os.path.join(pkg_hunter_gazebo, 'config', 'nav2_params.yaml'),
    description='Full path to the ROS2 parameters file to use'
)

# ⭕ After: behavior_server 노드 기동 및 라이프사이클 관리 대상 추가
start_behavior_server_node = Node(package='nav2_behaviors', executable='behavior_server', ...)
node_names = ['map_server', 'amcl', 'planner_server', 'controller_server', 'behavior_server', 'bt_navigator']
```
* **성과:** 모든 Nav2 라이프사이클 노드가 정상 `Active` 상태로 전이되며 맵 로딩 성공.

---

### 📌 Case 3. [모션 플래닝/제어] 아커만 차량의 제자리 회전(Spin) 버그 해결 및 Reeds-Shepp 전후진 궤적 튜닝
* **문제 현상:** 
  * Nav2 주행 중 코너 앞에서 로봇이 실제 자동차임에도 제자리 회전을 시도하며 앞바퀴만 꺾인 채 갇힘 (`Controller Failure`).
  * 후진이 필요한 좁은 코너에서 차량이 후진 경로를 따르지 못하고 급정거함.
* **근본 원인 분석:**
  1. **직각 경로 생성:** 기본 글로벌 플래너인 `NavfnPlanner (A*)`가 아커만의 최소 회전 반경을 무시하고 90도 직각 경로를 생성함.
  2. **불가능한 Spin 명령 하달:** 경로를 놓치자 Nav2 기본 복구 동작 1순위인 `Spin`(제자리 회전)이 발동됨.
  3. **후진 차단 설정:** 기본 제어기(`RPP`)에서 안전을 위해 후진(`allow_reversing: false`)과 전방 방향 정렬 회전(`use_rotate_to_heading: true`)이 강제되어 있었음.
* **해결 방안 및 조치:**
  * 전역 플래너를 전후진이 가능한 **`SmacPlannerHybrid (Hybrid-A*)` (Reeds-Shepp 모델)**로 교체.
  * 제어기(`RPP`)에서 제자리 회전을 차단하고 후진 주행을 허용하도록 파라미터 최적화.
  * 행동 트리에서 `spin` 플러그인을 제거하고 `backup`, `drive_on_heading`, `wait`로 대체.

#### 💻 [Before ❌ vs After ⭕ 코드 비교]
```yaml
# nav2_params.yaml

planner_server:
  ros__parameters:
    GridBased:
      # ❌ Before: 차동 구동용 플래너 (격자 지도 기반 직각 코너 경로 생성)
      # plugin: "nav2_navfn_planner/NavfnPlanner"

      # ⭕ After: 아커만 전용 Hybrid-A* 플래너 (최소 회전 반경 1.6m + 전후진 Reeds-Shepp 모션 모델)
      plugin: "nav2_smac_planner/SmacPlannerHybrid"
      motion_model_for_search: "REEDS_SHEPP"  # 👈 K-turn 후진 주행 경로 생성 가능
      minimum_turning_radius: 1.6

controller_server:
  ros__parameters:
    FollowPath:
      plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"
      # ❌ Before: 제자리 회전 시도 및 후진 금지
      # use_rotate_to_heading: true
      # allow_reversing: false

      # ⭕ After: 제자리 회전 원천 차단 및 후진 궤적 추종 허용
      use_rotate_to_heading: false
      allow_reversing: true
      lookahead_dist: 1.0      # 부드러운 스티어링을 위한 전방 주시 거리 튜닝
      min_lookahead_dist: 0.7

behavior_server:
  ros__parameters:
    # ❌ Before: 불가능한 제자리 회전 복구 동작 포함
    # behavior_plugins: ["spin", "backup", "drive_on_heading", "wait"]

    # ⭕ After: spin을 완전히 제거하고 아커만 차량 탈출 동작으로 재구성
    behavior_plugins: ["backup", "drive_on_heading", "wait"]
```
* **성과:** 제자리 회전 버그가 완전히 해결되었으며, 실제 자동차처럼 부드러운 호(Arc)를 그리거나 좁은 공간에서 후진(K-turn)을 활용하여 목적지까지 완벽 주행 성공.

---

## 5. 주행 결과 및 성능 검증 (Results & Demonstration)

### 📊 정량적 성능 지표
* **지도 해상도:** 5cm 정밀 격자 지도 구축 완료 (Map Resolution: `0.05 m/cell`)
* **최종 도착 정밀도:** RViz2 목표 지점 대비 오차 범위 **XY 0.25m / Yaw 0.25 rad 이내** 정확한 정차
* **자율주행 성공 판정:** `/navigate_to_pose/_action/status` 액션 상태 모니터링 (`status: 4` 성공 완료)
* **센서 데이터 스트리밍:** 3D-LiDAR 10 Hz, 전방 카메라 30 FPS 안정적 수신 유지

> 🎬 **시연 미디어:** `documents/videos/autonomous_navigation_01.gif`  
> *(RViz2 상에서 전역 경로 녹색선과 지역 경로 파란선을 따라 제자리 회전 없이 완만한 호를 그리며 목적지에 도달하는 자율주행 시연)*

---

## 6. 회고 및 향후 확장 로드맵 (Lessons Learned & Roadmap)

### 💡 엔지니어링 회고 (Key Takeaways)

#### 1. 경로 계획 알고리즘의 기구학적 진화 체득 (차동 구동 Navfn ➡️ 아커만 Hybrid-A*)
* **차동 구동(Diff-drive) 기반 기본 플래너(`NavfnPlanner` / 기본 A\*)의 한계:**
  * 청소기 로봇이나 터틀봇 같은 2륜 차동 구동 로봇은 언제든 제자리 360도 회전(Zero-radius Turn)이 가능함. 
  * 따라서 Nav2의 기본 플래너인 `NavfnPlanner`는 차량의 진입 방향각($\theta$)을 전혀 고려하지 않고, 2차원 $(x, y)$ 격자 지도 평면에서 픽셀 단위로 상하좌우 점을 잇는 최단 거리만 계산함.
  * 이로 인해 코너 모서리에서 **급격한 직각(90도) 꺾기 경로**가 생성됨. 차동 구동 로봇은 제자리 회전으로 이를 돌파할 수 있지만, **물리적인 최소 회전 반경($R=1.6\text{m}$)을 가진 아커만 차량은 직각 경로를 물리적으로 추종하지 못해 벽 충돌이나 제어 실패(`Controller Failure`)를 유발함**을 실증함.
* **아커만 전용 `Hybrid-A*`와 `Reeds-Shepp` 모션 모델로의 진화:**
  * 단순 2D 위치뿐만 아니라 **"로봇이 어느 방향(헤딩각 $\theta$)을 바라보고 진입하는가"**를 함께 계산하는 3차원 상태 공간 $(x, y, \theta)$ 기반의 **`Hybrid-A*` (SmacPlannerHybrid)**를 적용함.
  * 바둑판 격자 직선 대신 실제 자동차가 핸들을 꺾으며 이동하는 완만한 원호(Arc) 곡선을 연결하여 탐색함. 
  * 특히 전진 전용인 Dubins 모델 대신 **Reeds-Shepp 모션 모델**을 채택하여, 좁은 막다른 코너나 주차 구역에서도 K-턴(3-Point Turn, 전후진 반복)을 통해 스스로 탈출 궤적을 계획할 수 있도록 기구학적 한계를 근본적으로 해결함.

#### 2. 물리 기반 가상화의 중요성 (동역학과 하위 제어기의 일치)
* 상위 전역 플래너(`SmacPlannerHybrid`)가 아무리 완벽한 주행 궤적을 계산하더라도, 하위에서 실제 모터 속도와 조향각을 계산하는 **지역 경로 추종 제어기(RPP, Regulated Pure Pursuit)**와 가제보 물리 파라미터가 맞지 않으면 시스템이 붕괴된다는 사실을 체득함.
* 차체 하중으로 인한 조향축 슬립을 막기 위해 **PID 게인(`p: 100.0`)**을 투입하고, 급격한 핸들 꺾임을 방지하기 위해 **전방 주시 거리(Lookahead Distance: 0.7m ~ 2.0m)**를 튜닝함으로써, 물리 엔진(하드웨어) ↔ 제어 알고리즘(소프트웨어) 간의 동역학적 일치성을 확보하는 엔지니어링 감각을 기름.

#### 3. 센서 데이터 전처리의 파급력 (GIGO: Garbage In, Garbage Out)
* 고가의 16채널 3D-LiDAR(Velodyne VLP-16)를 사용하더라도, 하향 레이저가 바닥을 스캔하여 로봇을 따라다니는 '가짜 장애물'을 생성하는 현상을 규명함.
* 상위 알고리즘(SLAM, Costmap)에 원시 데이터를 그대로 넣으면 전체 시스템이 오판(맵 회전 및 드리프트)한다는 것을 확인하고, **기하학적 높이 슬라이싱(지면 필터링: `-0.1m ~ 1.0m`)**이라는 전처리 파이프라인의 결정적 중요성을 검증함.

---

### 🚀 향후 확장 로드맵 (PRD 6~10단계 연계)
* **[Step 06] Qt 대시보드 UI 연동:** 가상 리모컨 호출 버튼(`/remote_call`) 및 차량 상태(정상 주행, 고립, 주차 완료) 피드백 UI 통신 구현
* **[Step 07~08] Vision AI (YOLO) & 센서 융합 Fail-Safe:** 
  * 전방 카메라 영상(`/camera/image_raw`) 기반 딥러닝 객체 인식을 통해 주차 기둥/벽면 식별
  * 3D 점군과 융합하여 전방 경로가 완전히 차단되었을 때 비상 정지 및 경보음을 송출하는 안전(Fail-Safe) 모듈 구축
* **[Step 09] 강화학습(RL) 기반 초정밀 밀착 주차:** 
  * 호출 위치 반경 1m 진입 시 Nav2 일반 주행에서 RL 주차 에이전트로 제어권을 인계(Hand-over)
  * 기둥 및 벽면에 **오차 범위 10cm 이내**로 밀착 정차하는 정밀 제어기 구현
* **[Step 10] 시스템 통합 및 시나리오 종합 검증:** 통신 단절, 돌발 장애물 배치 등 극한 상황에서의 시스템 안전성 및 예외 처리 검증 완료
