# RM Step 05: ROS2 Nav2 기반 AgileX 자율주행 프레임워크 구축 및 검증 가이드

본 문서는 **[프로젝트 개발 로드맵]**의 **5단계: ROS2 Nav2 기반 AgileX 자율주행 프레임워크 구축**을 성공적으로 수행하기 위한 이론적 배경과 엔지니어링 상세 실행 가이드입니다.

---

## 1. 개요 및 이론적 배경

### 1.1. Nav2 (Navigation2) 내비게이션 스택의 구조
ROS 2의 **Nav2**는 자율주행 로봇이 위치를 스스로 추정하고, 지도를 기반으로 목적지까지 최적 경로를 계획하여 장애물을 회피하며 주행하도록 돕는 프레임워크입니다.
* **AMCL (Adaptive Monte Carlo Localization):** 확률적 파티클 필터를 이용해 실시간 센서 데이터(`/scan`)와 오도메트리(`/odom`)를 사전 지도(`/map`)와 대조함으로써 로봇의 위치\((x, y, \theta)\)를 추정합니다.
* **Map Server:** 4단계에서 저장한 정적 2D 점유 격자 지도(`parking_garage_map.yaml`, `.pgm`)를 Nav2 스택 전체에 퍼블리시합니다.
* **Costmap (비용 지도):**
  - **Global Costmap:** 전역 경로 계획을 위해 정적 맵 정보와 안전거리(Inflation Zone)를 표현합니다.
  - **Local Costmap:** 실시간 센서 데이터를 통해 정적 맵에 없던 동적/미지의 장애물을 실시간으로 감지하고 업데이트합니다.
* **Planner Server (전역 경로 계획기):** 출발지부터 목적지까지 충돌하지 않는 전체 최적 경로(Global Path)를 계산합니다.
* **Controller Server (지역 경로 제어기):** 전역 경로를 추종하면서 센서로 감지되는 실시간 장애물을 회피하기 위한 모터 제어 명령(`/cmd_vel` 또는 `ackermann_msgs`)을 계산합니다.
* **BT Navigator (Behavior Tree Navigator):** 유한 상태 머신보다 유연한 행동 트리(Behavior Tree) 구조를 통해 위치 추정, 경로 계획, 회피 동작 및 복구(Recovery) 절차의 전체 플로우를 총괄 관리합니다.

### 1.2. 아커만 조향 (Ackermann Steering)의 동역학적 제약 조건
* **차동 구동(Differential Drive)과의 차이:**
  - 차동 구동 로봇은 좌우 바퀴의 회전 방향을 반대로 하여 **제자리 회전(Zero-radius Turn)**이 가능합니다.
  - 반면 **AgileX Hunter**와 같은 아커만 조향 구조는 앞바퀴 회전 각도 한계(\(\delta_{max}\))로 인해 반드시 **최소 회전 반경(Minimum Turning Radius, \(R_{min}\))**을 가지며 제자리 회전이 불가능합니다.
* **Nav2 설정 시 필수 주의사항:**
  - 일반적인 Nav2 기본 설정(차동 구동용)을 그대로 적용하면 로봇이 주행 시작 시 제자리 회전을 시도하다 제어 에러(`Controller failure`)가 발생합니다.
  - 따라서 지역 제어기(Local Controller) 설정 시 **`use_rotate_to_heading: false`**로 설정하고, 회전 반경 제약 및 아커만 궤적을 추종하는 **`RegulatedPurePursuitController`**를 사용해야 합니다.

### 1.3. Regulated Pure Pursuit Controller의 원리
* **Pure Pursuit 기본 원리:** 로봇 앞쪽의 일정 거리(Lookahead Distance)에 위치한 전역 경로 상의 목표점(Lookahead Point)을 지정하고, 해당 점으로 다가가기 위한 곡률(Curvature) \(\gamma = \frac{2 \sin\alpha}{L}\)을 계산하여 조향각을 제어합니다.
* **Regulated (조절형) 기능:**
  - **곡률 기반 속도 감속:** 급격한 코너를 도는 아커만 차량의 이탈을 방지하기 위해 곡률이 클수록 주행 속도를 자동으로 줄입니다.
  - **장애물 근접 시 속도 감속:** Costmap 상 장애물과 가까워질수록 안전을 위해 속도를 줄입니다.
  - **제자리 회전 비활성화:** 아커만 구조 특성에 맞춰 제자리 제어 명령을 차단하고 연속적인 호(Arc) 이동 궤적을 만듭니다.

---

## 2. 사전 환경 및 작성/수정 대상 파일 경로

- **OS:** Ubuntu 22.04 LTS (Jammy Jellyfish)
- **ROS 2:** Humble Hawksbill
- **필수 ROS2 패키지:** `ros-humble-navigation2`, `ros-humble-nav2-bringup`, `ros-humble-pointcloud-to-laserscan`
- **Nav2 파라미터 파일 생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml` `[신규 작성]`
- **Nav2 스택 런치 파일 생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/navigation.launch.py` `[신규 작성]`
- **Nav2 통합 시뮬레이션 런치 파일 생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/bringup_sim_nav2.launch.py` `[신규 작성]`
- **패키지 빌드 설정 점검 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/CMakeLists.txt` `[파일 점검]`
- **입력 2D 주차장 지도 파일 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/maps/parking_garage_map.yaml` (.pgm) `[기존 참조]`
- **문서 본 내용 작성 경로:** `documents/RM_Step05_ROS2_Nav2_AgileX_Autonomous_Navigation_Guide.md` `[신규 작성]`

### 📄 전체 대상 파일 구분 및 작업 작업표

| 구분 | 파일/디렉토리 경로 | 역할 및 상세 설명 |
| :--- | :--- | :--- |
| **`[신규 작성]`** | `documents/RM_Step05_ROS2_Nav2_AgileX_Autonomous_Navigation_Guide.md` | 5단계 자율주행 프레임워크 구축 가이드 문서 |
| **`[신규 작성]`** | `ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml` | AMCL, Controller(PurePursuit), Costmap, Planner 파라미터 설정 |
| **`[신규 작성]`** | `ros2_ws/src/hunter_robot/hunter_gazebo/launch/navigation.launch.py` | Nav2 핵심 노드(amcl, map_server, planner, controller 등) 구동 런치 |
| **`[신규 작성]`** | `ros2_ws/src/hunter_robot/hunter_gazebo/launch/bringup_sim_nav2.launch.py` | Gazebo 시뮬레이션 + 3D LiDAR 스캔 변환 + Nav2 전체 통합 런치 |
| **`[파일 점검]`** | `ros2_ws/src/hunter_robot/hunter_gazebo/CMakeLists.txt` | `config`, `launch` 디렉토리 빌드 타겟 설치 명령 포함 상태 점검 |
| **`[기존 참조]`** | `ros2_ws/src/hunter_robot/hunter_gazebo/maps/parking_garage_map.yaml` | Step 04에서 완성된 정적 주차장 2D 점유 격자 지도 메타데이터 |
| **`[기존 참조]`** | `ros2_ws/src/hunter_robot/hunter_gazebo/maps/parking_garage_map.pgm` | Step 04에서 완성된 정적 주차장 2D 점유 격자 지도 흑백 이미지 |

---

## 3. 단계별 상세 실행 절차

### 3.1. [Step 5.1] Nav2 의존성 패키지 설치

터미널에서 ROS 2 Humble 버전의 Navigation2 자율주행 스택 및 Bringup 패키지를 설치합니다.

#### 📦 설치 대상 패키지 역할 및 설명
1. **`ros-humble-navigation2`**:
   - ROS 2 기반 자율주행을 위한 핵심 프레임워크 패키지입니다.
   - 전역 경로 계획(Planner Server), 지역 경로 제어(Controller Server), 실시간 2D/3D 비용 지도(Costmap), 위치 추정(AMCL), 행동 트리 관리자(BT Navigator) 등 자율주행 알고리즘 구현에 필요한 모든 기본 노드와 플러그인 라이브러리를 제공합니다.
2. **`ros-humble-nav2-bringup`**:
   - Nav2 프레임워크의 복잡한 여러 노드(Map Server, AMCL, Planner, Controller, Lifecycle Manager 등)를 묶어서 한 번에 구동하고 관리하기 위한 공식 **Bringup 런치 스크립트, 기본 파라미터 YAML 템플릿 및 설정 헬퍼 패키지**입니다.

```bash
sudo apt update
sudo apt install -y ros-humble-navigation2 ros-humble-nav2-bringup
```

---

### 3.2. [Step 5.2] Nav2 파라미터 파일 작성 (`nav2_params.yaml`) `[신규 작성]`

AgileX Hunter 아커만 로봇 구조와 주차장 지도의 특성에 맞춰 AMCL, Costmap, Planner 및 Controller 파라미터를 작성합니다.

* **생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml` `[신규 작성]`

```yaml
amcl:
  ros__parameters:
    use_sim_time: True
    alpha1: 0.2
    alpha2: 0.2
    alpha3: 0.2
    alpha4: 0.2
    alpha5: 0.2
    base_frame_id: "base_link"
    global_frame_id: "map"
    odom_frame_id: "odom"
    scan_topic: scan
    max_particles: 2000
    min_particles: 500
    update_min_d: 0.1
    update_min_a: 0.1

bt_navigator:
  ros__parameters:
    use_sim_time: True
    global_frame: map
    robot_base_frame: base_link
    odom_topic: odom
    bt_loop_duration: 10
    default_server_timeout: 20

controller_server:
  ros__parameters:
    use_sim_time: True
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.5
    min_theta_velocity_threshold: 0.001
    failure_tolerance: 0.3
    progress_checker_plugin: "progress_checker"
    goal_checker_plugins: ["general_goal_checker"]
    controller_plugins: ["FollowPath"]

    progress_checker:
      plugin: "nav2_controller::SimpleProgressChecker"
      required_movement_radius: 0.5
      movement_time_allowance: 10.0

    general_goal_checker:
      stateful: True
      plugin: "nav2_controller::SimpleGoalChecker"
      xy_goal_tolerance: 0.25
      yaw_goal_tolerance: 0.25

    # 🌟 아커만 조향 전용 Regulated Pure Pursuit Controller 설정
    FollowPath:
      plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"
      desired_linear_vel: 0.6
      lookahead_dist: 0.8
      min_lookahead_dist: 0.4
      max_lookahead_dist: 1.2
      lookahead_time: 1.5
      rotate_to_heading_angular_vel: 0.0
      transform_tolerance: 0.2
      use_velocity_scaled_lookahead_dist: true
      min_approach_linear_velocity: 0.05
      approach_velocity_scaling_dist: 0.6
      use_collision_detection: true
      max_allowed_time_to_collision_up_to_fast_stop: 1.0
      use_regulated_linear_velocity_scaling: true
      use_cost_regulated_linear_velocity_scaling: true
      cost_scaling_dist: 0.6
      cost_scaling_factor: 10.0
      regulated_linear_scaling_min_radius: 0.9
      regulated_linear_scaling_min_speed: 0.1
      use_rotate_to_heading: false  # 👈 필수: 아커만 제자리 회전 시도 방지

planner_server:
  ros__parameters:
    use_sim_time: True
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: false
      allow_unknown: true

local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 2.0
      global_frame: odom
      robot_base_frame: base_link
      use_sim_time: True
      rolling_window: true
      width: 4
      height: 4
      resolution: 0.05
      robot_radius: 0.45
      plugins: ["obstacle_layer", "inflation_layer"]
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: True
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: True
          marking: True
          data_type: "LaserScan"
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55

global_costmap:
  global_costmap:
    ros__parameters:
      update_frequency: 1.0
      publish_frequency: 1.0
      global_frame: map
      robot_base_frame: base_link
      use_sim_time: True
      robot_radius: 0.45
      resolution: 0.05
      track_unknown_space: true
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      static_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_subscribe_transient_local: True
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: True
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: True
          marking: True
          data_type: "LaserScan"
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55

map_server:
  ros__parameters:
    use_sim_time: True
    yaml_filename: ""

lifecycle_manager:
  ros__parameters:
    use_sim_time: True
    autostart: true
    node_names: ['map_server', 'amcl', 'planner_server', 'controller_server', 'behavior_server', 'bt_navigator']

behavior_server:
  ros__parameters:
    use_sim_time: True
    costmap_topic: local_costmap/costmap_raw
    footprint_topic: local_costmap/published_footprint
    cycle_frequency: 10.0
    behavior_plugins: ["spin", "backup", "drive_on_heading", "wait"]
    spin:
      plugin: "nav2_behaviors/Spin"
    backup:
      plugin: "nav2_behaviors/BackUp"
    drive_on_heading:
      plugin: "nav2_behaviors/DriveOnHeading"
    wait:
      plugin: "nav2_behaviors/Wait"
    global_frame: odom
    robot_base_frame: base_link
    transform_tolerance: 0.1
```

---

### 3.3. [Step 5.3] Nav2 실행 런치 파일 작성

#### 1) Nav2 스택 실행 런치 파일 (`navigation.launch.py`) `[신규 작성]`
* **생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/navigation.launch.py` `[신규 작성]`

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_hunter_gazebo = get_package_share_directory('hunter_gazebo')

    map_yaml_file = LaunchConfiguration('map')
    nav_params_file = LaunchConfiguration('nav_params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_hunter_gazebo, 'maps', 'parking_garage_map.yaml'),
        description='Full path to map yaml file to load')

    declare_nav_params_file_cmd = DeclareLaunchArgument(
        'nav_params_file',
        default_value=os.path.join(pkg_hunter_gazebo, 'config', 'nav2_params.yaml'),
        description='Full path to the ROS2 parameters file to use for all launched nodes')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    # Nav2 노드 리스트 실행
    start_map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[nav_params_file, {'yaml_filename': map_yaml_file, 'use_sim_time': use_sim_time}])

    start_amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])

    start_planner_node = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])

    start_controller_node = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])
    
    start_behavior_server_node = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])

    start_bt_navigator_node = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])

    start_lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time},
                    {'autostart': True},
                    {'node_names': ['map_server', 'amcl', 'planner_server', 'controller_server', 'behavior_server', 'bt_navigator']}])

    return LaunchDescription([
        declare_map_yaml_cmd,
        declare_nav_params_file_cmd,
        declare_use_sim_time_cmd,
        start_map_server_node,
        start_amcl_node,
        start_planner_node,
        start_controller_node,
        start_behavior_server_node,
        start_bt_navigator_node,
        start_lifecycle_manager
    ])
```

#### 2) Gazebo + 센서 변환 + Nav2 통합 시뮬레이션 런치 파일 (`bringup_sim_nav2.launch.py`) `[신규 작성]`
* **생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/bringup_sim_nav2.launch.py` `[신규 작성]`

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_hunter_gazebo = get_package_share_directory('hunter_gazebo')

    # 1. Gazebo 월드 런치 (Hunter 모델 스폰 포함)
    launch_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_hunter_gazebo, 'launch', 'launch_sim.launch.py')
        )
    )

    # 2. 3D LiDAR -> 2D LaserScan 변환 노드
    start_pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        output='screen',
        parameters=[{
            'target_frame': 'velodyne_link',
            'transform_tolerance': 0.01,
            'min_height': -0.1,
            'max_height': 1.0,
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.0087,
            'scan_time': 0.1,
            'range_min': 0.3,
            'range_max': 20.0,
            'use_sim_time': True
        }],
        remappings=[('cloud_in', '/points_raw'), ('scan', '/scan')]
    )

    # 3. Nav2 런치 포함
    launch_nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_hunter_gazebo, 'launch', 'navigation.launch.py')
        )
    )

    return LaunchDescription([
        launch_sim,
        start_pointcloud_to_laserscan_node,
        launch_nav2
    ])
```

---

### 3.4. [Step 5.4] CMakeLists.txt 점검 및 패키지 빌드 `[파일 점검]`

* **대상 파일:** `ros2_ws/src/hunter_robot/hunter_gazebo/CMakeLists.txt` `[파일 점검]`
* **확인 사항:** `install(DIRECTORY config launch worlds maps DESTINATION share/${PROJECT_NAME})` 구문이 작성되어 있어 신규 생성한 파일들이 자동으로 빌드 타겟에 포함됩니다.

```bash
cd ros2_ws
colcon build
source install/setup.bash
```

---

### 3.5. [Step 5.5] Nav2 주행 시뮬레이션 및 RViz2 자율주행 검증

> [!NOTE]
> 1번, 2번 터미널을 각각 열어 순서대로 구동합니다.

#### 1) [터미널 1] 통합 Nav2 시뮬레이션 실행
```bash
cd ros2_ws
source install/setup.bash
ros2 launch hunter_gazebo bringup_sim_nav2.launch.py
```

#### 2) [터미널 2] RViz2 시각화 및 자율주행 명령어 지정
```bash
source install/setup.bash
rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz
```

#### 3) RViz2 상에서 주행 명령 수행 절차 (🌟 필수 실행 과정)
1. **RViz2 디스플레이 추가:** `Map` (Global/Local Costmap), `Path` (Global/Local Plan), `Particle Cloud` (AMCL) 디스플레이 항목을 활성화합니다.
2. **초기 위치 지정 (2D Pose Estimate):**
   - 상단 툴바의 **`2D Pose Estimate`** 버튼을 클릭합니다.
   - Gazebo 월드 내 Hunter 로봇이 위치한 주차장 초기 지점을 클릭하고 차체 방향으로 마우스를 끌어 방향 튜닝을 완료합니다. (AMCL 파티클이 수렴함)
3. **자율주행 목적지 지정 (2D Goal Pose):**
   - 상단 툴바의 **`2D Goal Pose`** 버튼을 클릭합니다.
   - 주차장 기둥 반대편 통로나 주차 공간 내부 지점을 클릭하고 마우스를 끌어 도착 시 방향을 지정합니다.
4. **자율주행 궤적 모니터링:**
   - 로봇이 제자리 회전을 시도하지 않고 아커만 곡선을 그리며 이동하는지 확인합니다.
   - 이동 중 전방 장애물(기둥/벽)을 감지하고 전역/지역 경로가 유연하게 장애물을 회피하여 최종 목적지 허용 오차 내에 도착하는지 검증합니다.

---

## 4. 검증 및 트러블슈팅 (Troubleshooting)

### 4.1. 결과 검증 기준
1. **AMCL 파티클 수렴:** 2D Pose Estimate 지정 후 로봇 주행에 따라 AMCL 파티클이 하나로 집약되며 가상 월드 위치와 정적 지도의 위치가 정확히 동기화되는가?
2. **Costmap 표현:** Global/Local Costmap 상에 주차장 기둥과 벽이 붉은색/보라색 인플레이션 안전 지대로 올바르게 표출되는가?
3. **아커만 궤적 주행:** 2D Goal Pose 명령 시 제자리 회전 없이 아커만 호(Arc)를 따라 장애물을 피해 목적지 허용 오차(XY 0.25m 이내)에 정차하는가?

### 4.2. 주요 트러블슈팅 가이드

* **문제 1: 2D Goal Pose 명령을 내렸으나 로봇이 움직이지 않고 터미널에 `[controller_server]: Failed to produce control command` 에러 반복**
  - **원인:** Nav2 Controller 파라미터 중 `use_rotate_to_heading: true`로 되어 있어 차동 구동처럼 제자리 회전을 시도하다 실패함.
  - **해결:** `nav2_params.yaml` 내 `FollowPath.use_rotate_to_heading: false` 설정 확인.

* **문제 2: `[bt_navigator]: Waiting for amcl to be ready` 문구가 지속되며 진행되지 않는 경우**
  - **원인:** AMCL 초기 위치가 설정되지 않았거나 Lifecycle Manager에서 AMCL 노드 활성화 실패.
  - **해결:** RViz2 상에서 **`2D Pose Estimate`**를 지정해주어 AMCL 노드에 초기 위치(Pose) 정보를 전달해야 합니다.

* **문제 3: 주행 도중 로봇이 벽이나 기둥 주변에서 지나치게 멈칫거리는 현상**
  - **원인:** `inflation_radius` 또는 `cost_scaling_factor` 값이 지나치게 높아 차체 패스 공간을 통과 불가능한 영역으로 인지함.
  - **해결:** `nav2_params.yaml`의 `inflation_radius` 값을 `0.55m` 수준으로 미세 조정합니다.
