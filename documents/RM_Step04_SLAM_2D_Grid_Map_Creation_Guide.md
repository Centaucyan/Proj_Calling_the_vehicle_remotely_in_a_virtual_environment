# RM Step 04: SLAM을 통한 정적 2D 격자 지도(Map) 작성 및 검증 가이드

본 문서는 **[프로젝트 개발 로드맵]**의 **4단계: SLAM을 통한 정적 2D 격자 지도(Map) 작성 (`parking_garage.world`)**을 성공적으로 수행하기 위한 엔지니어링 상세 실행 가이드입니다.

---

## 1. 개요 및 목표

* **목표:** 3단계에서 구축한 가상 주차장 월드(`parking_garage.world`) 환경에서 AgileX Hunter 로봇의 센서(3D-LiDAR `/scan` 토픽 및 오도메트리 `/odom`)와 `slam_toolbox` 패키지를 연동하여 주차장 전체의 2D 점유 격자 지도(Occupancy Grid Map)를 생성하고 저장합니다.
* **주요 검증 요소:**
  - `slam_toolbox` (Online Async SLAM) 노드의 정상 연동 및 `/map` 토픽 퍼블리시 확인
  - `teleop_twist_keyboard` 수동 조종을 통한 주차장 외벽, 콘크리트 기둥, 주차 구획 장애물 공간 스캔 및 매핑
  - RViz2 상에서 차량 주행에 따른 실시간 지도 확장 및 루프 클로저(Loop Closure) 동작 확인
  - `nav2_map_server`의 `map_saver_cli`를 이용한 정적 맵 파일(`parking_garage_map.yaml`, `parking_garage_map.pgm`) 정상 저장 및 노이즈 검증

---

## 2. 사전 환경 및 생성 대상 파일 경로

- **OS:** Ubuntu 22.04 LTS (Jammy Jellyfish)
- **ROS 2:** Humble Hawksbill
- **필수 ROS2 패키지:** `slam-toolbox`, `nav2-map-server`
- **SLAM 설정 파일 생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/mapper_params_online_async.yaml`
- **SLAM 매핑 런치 파일 생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/slam_mapping.launch.py`
- **최종 지도 저장 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/maps/parking_garage_map.yaml` (.pgm)

---

## 3. 단계별 상세 실행 절차

### 3.1. [Step 4.1] SLAM 의존성 패키지 설치 확인

SLAM 및 맵 저장 도구가 설치되어 있지 않은 경우 설치합니다.

```bash
sudo apt update
sudo apt install -y ros-humble-slam-toolbox ros-humble-nav2-map-server
```

---

### 3.2. [Step 4.2] `slam_toolbox` 파라미터 파일 신규 작성 (`mapper_params_online_async.yaml`)

AgileX Hunter의 센서 프레임(`base_link`, `odom`, `/scan`)에 맞춰 `slam_toolbox` 파라미터 설정을 구성합니다.

* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/mapper_params_online_async.yaml`

```yaml
slam_toolbox:
  ros__parameters:
    # Solver settings
    solver_plugin: solver_plugins::CspaSolver
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

### 3.3. [Step 4.3] SLAM 및 Gazebo 통합 런치 파일 신규 작성 (`slam_mapping.launch.py`)

주차장 월드 Gazebo 구동과 `slam_toolbox` 노드를 동시에 실행할 수 있는 통합 런치 스크립트를 생성합니다.

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

    # 1. Gazebo 주차장 월드 런치 포함
    launch_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_hunter_gazebo, 'launch', 'launch_sim.launch.py')
        )
    )

    # 2. SLAM Toolbox 설정 파일 지정
    slam_config_file = os.path.join(pkg_hunter_gazebo, 'config', 'mapper_params_online_async.yaml')

    # 3. slam_toolbox 노드 실행
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
        start_async_slam_toolbox_node
    ])
```

---

### 3.4. [Step 4.4] CMakeLists.txt 파일 업데이트 및 패키지 빌드

신규 작성된 `config`, `launch`, `worlds`, `maps` 디렉토리가 `colcon build` 시 `install` 디렉토리로 정상 복사되도록 `CMakeLists.txt`를 업데이트합니다.

```cmake
install(
  DIRECTORY config launch worlds maps
  DESTINATION share/${PROJECT_NAME}
)
```

---

### 3.5. [Step 4.5] 주차장 월드 매핑 주행 및 맵 저장

#### 1) SLAM 통합 런치 실행
```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch hunter_gazebo slam_mapping.launch.py
```

#### 2) 키보드 제어로 주차장 전체 구역 조종 주행
```bash
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
* 로봇을 천천히 주차장 내부 통로, 기둥 둘레, 구획선 근처로 이동시켜 2D 격자 지도를 완성합니다.

#### 3) 완성된 2D 지도 저장
```bash
source install/setup.bash
mkdir -p src/hunter_robot/hunter_gazebo/maps
ros2 run nav2_map_server map_saver_cli -f src/hunter_robot/hunter_gazebo/maps/parking_garage_map
```
* 결과물: `parking_garage_map.yaml` 및 `parking_garage_map.pgm` 생성 확인

---

## 4. 검증 및 결과 확인

1. **RViz2 시각화 검증:** `Map` 디스플레이를 추가하여 `/map` 토픽의 2D 점유 격자 지도가 기둥과 외벽을 정확한 직선/직각형태로 표현하는지 확인
2. **맵 저장 파일 검증:** `parking_garage_map.pgm` 이미지 파일을 열어 외벽 및 4개의 기둥 장애물이 왜곡 없이 뚜렷하게 맵화되었는지 확인
