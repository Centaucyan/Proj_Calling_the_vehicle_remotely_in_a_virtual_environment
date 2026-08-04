# RM Step 04: SLAM을 통한 정적 2D 격자 지도(Map) 작성 및 검증 가이드

본 문서는 **[프로젝트 개발 로드맵]**의 **4단계: SLAM을 통한 정적 2D 격자 지도(Map) 작성 (`parking_garage.world`)**을 성공적으로 수행하기 위한 엔지니어링 상세 실행 가이드입니다.

---

## 1. 개요 및 목표

* **목표:** 3단계에서 구축한 가상 주차장 월드(`parking_garage.world`) 환경에서 AgileX Hunter 로봇의 센서(3D-LiDAR `/scan` 토픽 및 아커만 오도메트리 `/odom`)와 `slam_toolbox` 패키지를 연동하여 주차장 전체의 2D 점유 격자 지도(Occupancy Grid Map)를 생성하고 저장합니다.
* **주요 검증 요소:**
  - Step 02에서 구축한 `ackermann_steering_controller` 기반의 오차 없는 2D 격자 지도 매핑 수행
  - `slam_toolbox` (Online Async SLAM) 노드의 정상 연동 및 `/map` 토픽 퍼블리시 확인
  - `teleop_twist_keyboard` 수동 조종을 통한 주차장 외벽, 콘크리트 기둥, 주차 구획 장애물 공간 스캔 및 매핑
  - RViz2 상에서 차량 주행에 따른 실시간 지도 확장 및 루프 클로저(Loop Closure) 동작 확인
  - `nav2_map_server`의 `map_saver_cli`를 이용한 정적 맵 파일(`parking_garage_map.yaml`, `parking_garage_map.pgm`) 정상 저장 및 노이즈 검증

---

## 2. 사전 환경 및 생성 대상 파일 경로

- **OS:** Ubuntu 22.04 LTS (Jammy Jellyfish)
- **ROS 2:** Humble Hawksbill
- **필수 ROS2 패키지:** `slam-toolbox`, `nav2-map-server`, `pointcloud-to-laserscan`
- **SLAM 설정 파일 생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/mapper_params_online_async.yaml`
- **SLAM 매핑 런치 파일 생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/slam_mapping.launch.py`
- **최종 지도 저장 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/maps/parking_garage_map.yaml` (.pgm)

---

## 3. 단계별 상세 실행 절차

### 3.1. [Step 4.1] SLAM 의존성 패키지 설치 확인

SLAM, 맵 저장 도구 및 3D PointCloud -> 2D LaserScan 변환 패키지가 설치되어 있지 않은 경우 설치합니다.

#### 📦 설치 대상 패키지 역할 및 설명
1. **`ros-humble-slam-toolbox`**: 2D 점유 격자 지도(Occupancy Grid Map)를 실시간으로 구축(Online Async SLAM)하고 그래프 최적화(Ceres Solver) 및 루프 클로저(Loop Closure)를 수행하는 2D SLAM 알고리즘 패키지입니다.
2. **`ros-humble-nav2-map-server`**: 완성된 SLAM 지도 데이터를 정적 맵 파일(`parking_garage_map.yaml`, `.pgm`)로 저장할 수 있는 CLI 도구(`map_saver_cli`) 및 주행 시 지도를 불러와 퍼블리시하는 노드를 제공합니다.
3. **`ros-humble-pointcloud-to-laserscan`**: 3D LiDAR에서 입수되는 3D 포인트 클라우드 데이터(`/points_raw`)를 원하는 높이 슬라이스로 잘라 2D SLAM 노드가 수신 가능한 2D 레이저 스캔(`/scan`) 토픽으로 실시간 가공/변환하는 노드입니다.

```bash
sudo apt update
sudo apt install -y ros-humble-slam-toolbox ros-humble-nav2-map-server ros-humble-pointcloud-to-laserscan
```

---

### 3.2. [Step 4.2] 컨트롤러 점검 및 `slam_toolbox` 파라미터 파일 작성

#### 1) 아커만 로봇 컨트롤러 오도메트리 파라미터 임시 변경 (매핑용 🌟)
Step 02에서 구축한 아커만 전용 제어기(`ackermann_controllers.yaml`)의 기본 설정은 실제 엔코더 값을 반영하는 `open_loop: false`입니다. 
하지만 아커만 차량 특성상 가제보 내에서 회전 시 바퀴가 끌리는 슬립(Scrubbing) 현상이 발생하면, 오도메트리 노이즈로 인해 SLAM 지도의 벽면이 겹치거나 맵이 붕괴될 수 있습니다. 
따라서 **성공적이고 깔끔한 2D 지도 작성을 위해, 매핑 과정에서만 임시로 `open_loop: true`로 변경**하여 오도메트리가 명령어(`cmd_vel`)대로 부드럽게 생성되도록 속입니다. (매핑 완료 후 반드시 다시 원복해야 합니다.)

* **수정 대상 파일:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/ackermann_controllers.yaml`
* **변경 사항:** `open_loop` 항목을 `true`로 변경하고, `enable_odom_tf`가 `true`인지 확인합니다.

```yaml
ackermann_steering_controller:
  ros__parameters:
    ...
    odom_frame_id: odom
    base_frame_id: base_link
    enable_odom_tf: true  # 👈 odom -> base_link TF 브로드캐스팅 확인
    open_loop: true       # 🌟 매핑을 위해 일시적으로 true로 변경 (부드러운 오도메트리 생성)
```

#### 2) `slam_toolbox` 파라미터 파일 작성 (`mapper_params_online_async.yaml`)
AgileX Hunter의 센서 프레임(`base_link`, `odom`, `/scan`)에 맞춰 `slam_toolbox` 파라미터를 작성합니다. (ROS 2 Humble 표준 `CeresSolver` 엔진 사용)

* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/mapper_params_online_async.yaml`

```yaml
slam_toolbox:
  ros__parameters:
    # Solver settings (ROS 2 Humble 표준 CeresSolver 사용)
    solver_plugin: solver_plugins::CeresSolver
    ceres_linear_solver: SPARSE_NORMAL_CHOLESKY
    ceres_preconditioner: SCHUR_JACOBI
    ceres_trust_strategy: LEVENBERG_MARQUARDT
    ceres_dogleg_type: TRADITIONAL_DOGLEG
    ceres_loss_function: None

    # ROS Frame & Topic settings
    odom_frame: odom
    map_frame: map
    base_frame: base_link
    scan_topic: /scan
    use_map_saver: true
    mode: mapping

    # Transform & Timing
    transform_timeout: 0.2
    tf_buffer_duration: 30.
    stack_size_to_use: 40000000
    enable_interactive_mode: true

    # General Parameters
    use_scan_matching: true
    use_scan_barycenter: true
    minimum_travel_distance: 0.1
    minimum_travel_heading: 0.1
    scan_buffer_size: 10
    scan_buffer_maximum_scan_distance: 10.0
    link_match_minimum_response_fine: 0.1
    link_scan_maximum_distance: 1.5
    loop_search_maximum_distance: 3.0
    do_loop_closing: true

    # Map resolution settings
    resolution: 0.05
    max_laser_range: 20.0
```

---

### 3.3. [Step 4.3] SLAM 및 Gazebo 통합 런치 파일 작성 (`slam_mapping.launch.py`)

주차장 월드 Gazebo 구동(아커만 제어기 포함), 3D PointCloud -> 2D LaserScan 변환 노드, 그리고 `slam_toolbox` 노드를 동시에 실행할 수 있는 통합 런치 스크립트를 작성합니다.

* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/slam_mapping.launch.py`

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_hunter_gazebo = get_package_share_directory('hunter_gazebo')

    # 1. Gazebo 주차장 월드 런치 포함 (아커만 제어기 스포너 구동)
    launch_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_hunter_gazebo, 'launch', 'launch_sim.launch.py')
        )
    )

    # 2. 3D PointCloud (/points_raw) -> 2D LaserScan (/scan) 변환 노드
    start_pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        output='screen',
        parameters=[{
            'target_frame': 'velodyne_link',
            'transform_tolerance': 0.01,
            'min_height': -0.1,  # 🌟 -0.3에서 상향 조정: 바닥 노이즈를 장애물로 인식하는 문제 원천 차단
            'max_height': 1.0,
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.0087,
            'scan_time': 0.1,
            'range_min': 0.3,
            'range_max': 20.0,
            'use_sim_time': True
        }],
        remappings=[
            ('cloud_in', '/points_raw'),
            ('scan', '/scan')
        ]
    )

    # 3. SLAM Toolbox 설정 파일 지정
    slam_config_file = os.path.join(pkg_hunter_gazebo, 'config', 'mapper_params_online_async.yaml')

    # 4. slam_toolbox 노드 실행
    start_async_slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_config_file,
            {'use_sim_time': True}
        ]
    )

    return LaunchDescription([
        launch_sim,
        start_pointcloud_to_laserscan_node,
        start_async_slam_toolbox_node
    ])
```

---

### 3.4. [Step 4.4] CMakeLists.txt 파일 업데이트 및 패키지 빌드

`config`, `launch`, `worlds`, `maps` 디렉토리가 `colcon build` 시 `install` 디렉토리로 정상 복사되도록 `CMakeLists.txt`를 업데이트합니다.

```cmake
install(
  DIRECTORY config launch worlds maps
  DESTINATION share/${PROJECT_NAME}
)
```

---

### 3.5. [Step 4.5] 주차장 월드 매핑 주행 및 맵 저장

> [!NOTE]
> 아래의 각 단계(1~4번)는 동시 구동을 위해 반드시 **서로 다른 개별 터미널**을 열어 각각 실행해야 합니다.

#### 1) [터미널 1] SLAM 통합 런치 실행
```bash
cd ros2_ws
colcon build
source install/setup.bash
ros2 launch hunter_gazebo slam_mapping.launch.py
```

#### 2) [터미널 2] RViz2 구동 및 실시간 2D 지도 시각화 (선택 및 권장 🌟)
```bash
source install/setup.bash
rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz
```
* **RViz2 디스플레이 설정:** `Map` 디스플레이 추가 후 Topic을 `/map`으로 지정하고 Durability Policy를 `Transient Local`로 확인.

#### 3) [터미널 3] 키보드 제어로 주차장 전체 구역 조종 주행
```bash
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
* 아커만 조향 특성에 맞춰 차량을 주차장 통로 및 4개 기둥 둘레로 이동시켜 지도를 완성합니다.

#### 4) [터미널 4] 완성된 2D 지도 저장 (주행 완료 후)
```bash
source install/setup.bash
mkdir -p src/hunter_robot/hunter_gazebo/maps
ros2 run nav2_map_server map_saver_cli -f src/hunter_robot/hunter_gazebo/maps/parking_garage_map
```

---

### 3.6. [Step 4.6] 맵 작성 완료 후 오도메트리 파라미터 원복 (자율주행 준비) 🌟

성공적으로 지도를 파일로 저장했다면, 다음 단계인 **[Step 5] 자율주행(Nav2)**을 위해 변경했던 파라미터를 반드시 원래 상태로 되돌려야 합니다.
자율주행 시에는 로봇이 장애물에 부딪히거나 바퀴가 미끄러졌을 때 그 물리적 상태를 위치 추정 알고리즘(AMCL)이 알아차려야 합니다. 따라서 가상 궤적(`true`)이 아닌 실제 바퀴 회전량 기반(`false`)을 사용해야 로봇 이동 시 지도가 틀어지거나 돌아가는(Drift) 현상을 막을 수 있습니다.

* **수정 대상 파일:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/ackermann_controllers.yaml`
* **복구 내용:**
```yaml
ackermann_steering_controller:
  ros__parameters:
    # ... (생략) ...
    open_loop: false  # 🌟 다시 false로 원복하여 자율주행(Nav2) 준비 완료
```

---

## 4. 검증 및 트러블슈팅 (Troubleshooting)

### 4.1. 결과 검증
1. **RViz2 시각화 검증:** `Map` 디스플레이를 추가하여 `/map` 토픽의 2D 점유 격자 지도가 기둥과 외벽을 정확한 직선/직각형태로 표현하는지 확인
2. **맵 저장 파일 검증:** 저장된 `parking_garage_map.pgm` 이미지 파일을 열어 외벽 및 4개의 기둥 장애물이 왜곡 없이 뚜렷하게 맵화되었는지 확인
   > 💡 **[Tip] PGM 맵 파일 여는 방법 (우분투 환경)**
   > PGM 파일은 단순한 흑백 이미지 포맷이지만 일반적인 더블클릭으로는 텍스트로 깨져서 열릴 수 있습니다. 이때 터미널에서 우분투 기본 이미지 뷰어인 `eog` 명령어를 사용하면 즉시 확인할 수 있습니다.
   > ```bash
   > cd Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/hunter_robot/hunter_gazebo/maps
   >
   > eog parking_garage_map.pgm
   > ```

### 4.2. 트러블슈팅 가이드
* **문제 1: `slam_toolbox` 구동 시 `Failed to create solver_plugins::CspaSolver` 에러 발생**
  - **원인:** ROS 2 Humble 버전에서 CspaSolver가 제외되고 CeresSolver가 표준으로 탑재됨.
  - **해결:** `mapper_params_online_async.yaml` 5번 줄의 솔버를 `solver_plugin: solver_plugins::CeresSolver`로 변경.

* **문제 2: RViz2 Fixed Frame 목록에 `odom`이나 `map`이 표시되지 않고 `/map` 토픽이 생성되지 않는 경우**
  - **원인:** `hunter_gazebo/config/ackermann_controllers.yaml` 내 `enable_odom_tf` 옵션이 `false`로 설정됨.
  - **해결:** `ackermann_controllers.yaml` 파일 내 `enable_odom_tf: true`로 수정 후 패키지 재빌드.
