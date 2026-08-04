# RM Step 03: Gazebo 가상 주차장 월드(World) 환경 구축 및 검증 가이드

본 문서는 **[프로젝트 개발 로드맵]**의 **3단계: Gazebo 가상 주차장 월드(World) 환경 구축 및 검증 (`parking_garage.world`)**을 성공적으로 수행하기 위한 엔지니어링 상세 실행 가이드입니다.

---

## 1. 개요 및 목표

* **목표:** AgileX Hunter 2.0 차체 규격(약 1.0m × 0.75m)에 맞춘 흰색 주차 구획선(1.5m × 2.2m), 외벽 및 진입로, 선행 주차 차량/라바콘 장애물, 그리고 PRD 요구사항(Vision AI 및 RL 정밀 밀착 주차)을 충족하는 콘크리트 기둥 타겟이 포함된 전용 가상 주차장 월드(`parking_garage.world`)를 구축하고 검증합니다.
* **주요 검증 요소:**
  - Gazebo 시뮬레이터 상에 외벽(입구 갭 포함), 흰색 주차 구획선, 주차 기둥, 장애물 요소가 배치된 `parking_garage.world` 정상 로딩 여부
  - 주차장 월드 입구`(0, -8, 0.25)`에 AgileX Hunter (3D-LiDAR 및 카메라 통합 로봇) 스폰 정상 구동 여부
  - RViz2 상에서 주차 구획선 및 벽/기둥 형태가 3D-LiDAR 포인트 클라우드(`/points_raw`)와 카메라 이미지(`/camera/image_raw`)로 선명하게 렌더링되는지 모니터링
  - `teleop_twist_keyboard` 주행을 통한 주차선 내 차량 주차 및 벽/기둥 장애물 물리 충돌 및 오도메트리 반영 검증

---

## 2. 사전 환경 및 파일 경로

- **OS:** Ubuntu 22.04 LTS (Jammy Jellyfish)
- **ROS 2:** Humble Hawksbill
- **시뮬레이터:** Gazebo Classic (v11) & RViz2
- **신규 월드 파일 생성 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/worlds/parking_garage.world`
- **런치 스크립트 수정 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/launch_sim.launch.py`
- **CMake 빌드 설정 수정 경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/CMakeLists.txt`

---

## 3. 단계별 상세 실행 절차

### 3.1. [Step 3.1] AgileX 맞춤형 가상 주차장 World SDF 파일 신규 작성 (`parking_garage.world`)

AgileX Hunter 규격 맞춤 주차 구획선(가로 1.5m × 세로 2.2m), 외벽, 입구, 기둥 및 장애물이 수록된 Gazebo World SDF 정의 파일을 생성합니다.

* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_gazebo/worlds/parking_garage.world`

```xml
<?xml version="1.0" ?>
<sdf version="1.6">
  <world name="parking_garage">
    
    <!-- 태양광 조명 설정 -->
    <include>
      <uri>model://sun</uri>
    </include>

    <!-- 아스팔트 지면 평면 -->
    <include>
      <uri>model://ground_plane</uri>
    </include>

    <!-- 물리 엔진 파라미터 (ODE) -->
    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
    </physics>

    <!-- ==================== 1. 외벽 및 입구 (Outer Walls & Entrance) ==================== -->
    <!-- North Wall -->
    <model name="wall_north">
      <pose>0 12.0 1.25 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>24.0 0.3 2.5</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>24.0 0.3 2.5</size></box></geometry>
          <material>
            <ambient>0.85 0.85 0.85 1</ambient>
            <diffuse>0.85 0.85 0.85 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- East Wall -->
    <model name="wall_east">
      <pose>12.0 0 1.25 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>0.3 24.0 2.5</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>0.3 24.0 2.5</size></box></geometry>
          <material>
            <ambient>0.85 0.85 0.85 1</ambient>
            <diffuse>0.85 0.85 0.85 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- West Wall -->
    <model name="wall_west">
      <pose>-12.0 0 1.25 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>0.3 24.0 2.5</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>0.3 24.0 2.5</size></box></geometry>
          <material>
            <ambient>0.85 0.85 0.85 1</ambient>
            <diffuse>0.85 0.85 0.85 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- South Wall Left (입구 좌측 벽) -->
    <model name="wall_south_left">
      <pose>-7.5 -12.0 1.25 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>9.0 0.3 2.5</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>9.0 0.3 2.5</size></box></geometry>
          <material>
            <ambient>0.85 0.85 0.85 1</ambient>
            <diffuse>0.85 0.85 0.85 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- South Wall Right (입구 우측 벽) -->
    <model name="wall_south_right">
      <pose>7.5 -12.0 1.25 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>9.0 0.3 2.5</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>9.0 0.3 2.5</size></box></geometry>
          <material>
            <ambient>0.85 0.85 0.85 1</ambient>
            <diffuse>0.85 0.85 0.85 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- ==================== 2. PRD 정밀 주차용 콘크리트 기둥 (Pillars) ==================== -->
    <!-- 주차 타겟 기둥 1 (Target Pillar 1) -->
    <model name="target_pillar_1">
      <pose>4.0 3.0 1.25 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>0.8 0.8 2.5</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>0.8 0.8 2.5</size></box></geometry>
          <material>
            <ambient>0.2 0.4 0.8 1</ambient>
            <diffuse>0.2 0.4 0.8 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- 주차 타겟 기둥 2 (Target Pillar 2) -->
    <model name="target_pillar_2">
      <pose>-4.0 3.0 1.25 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>0.8 0.8 2.5</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>0.8 0.8 2.5</size></box></geometry>
          <material>
            <ambient>0.2 0.4 0.8 1</ambient>
            <diffuse>0.2 0.4 0.8 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- ==================== 3. AgileX 맞춤형 흰색 주차 구획선 (Parking Bay Lines) ==================== -->
    <!-- Central Parking Bays (Center Left Row) -->
    <model name="parking_lines_center">
      <pose>0 0 0.002 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <!-- Center Backbone Line -->
        <visual name="line_center_back">
          <pose>0 0 0 0 0 0</pose>
          <geometry><box><size>0.08 10.0 0.001</size></box></geometry>
          <material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse></material>
        </visual>
        <!-- Horizontal Bay Divider Lines (1.5m x 2.2m bays) -->
        <visual name="line_div_1"><pose>0 5.0 0 0 0 0</pose><geometry><box><size>4.4 0.08 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
        <visual name="line_div_2"><pose>0 3.5 0 0 0 0</pose><geometry><box><size>4.4 0.08 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
        <visual name="line_div_3"><pose>0 2.0 0 0 0 0</pose><geometry><box><size>4.4 0.08 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
        <visual name="line_div_4"><pose>0 0.5 0 0 0 0</pose><geometry><box><size>4.4 0.08 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
        <visual name="line_div_5"><pose>0 -1.0 0 0 0 0</pose><geometry><box><size>4.4 0.08 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
        <visual name="line_div_6"><pose>0 -2.5 0 0 0 0</pose><geometry><box><size>4.4 0.08 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
        <visual name="line_div_7"><pose>0 -4.0 0 0 0 0</pose><geometry><box><size>4.4 0.08 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
        <visual name="line_div_8"><pose>0 -5.5 0 0 0 0</pose><geometry><box><size>4.4 0.08 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
        <!-- Outer Boundary Lines -->
        <visual name="line_outer_left"><pose>-2.2 -0.25 0 0 0 0</pose><geometry><box><size>0.08 10.5 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
        <visual name="line_outer_right"><pose>2.2 -0.25 0 0 0 0</pose><geometry><box><size>0.08 10.5 0.001</size></box></geometry><material><ambient>1 1 1 1</ambient></material></visual>
      </link>
    </model>

    <!-- ==================== 4. 주차 장애물 (Parked Vehicles & Cones) ==================== -->
    <!-- 주차 구획 내 선행 주차 차량 1 (Parked Car 1) -->
    <model name="parked_car_1">
      <pose>-1.1 2.75 0.4 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>1.6 1.0 0.8</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>1.6 1.0 0.8</size></box></geometry>
          <material>
            <ambient>0.1 0.3 0.7 1</ambient> <!-- 파란색 세단 장애물 -->
            <diffuse>0.1 0.3 0.7 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- 주차 구획 내 선행 주차 차량 2 (Parked Car 2) -->
    <model name="parked_car_2">
      <pose>1.1 -1.75 0.4 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>1.6 1.0 0.8</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>1.6 1.0 0.8</size></box></geometry>
          <material>
            <ambient>0.6 0.6 0.6 1</ambient> <!-- 은색 SUV 장애물 -->
            <diffuse>0.6 0.6 0.6 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- 라바콘 장애물 (Traffic Cone) -->
    <model name="traffic_cone_1">
      <pose>-1.1 -0.25 0.25 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><cylinder radius="0.15" length="0.5"/></geometry>
        </collision>
        <visual name="visual">
          <geometry><cylinder radius="0.15" length="0.5"/></geometry>
          <material>
            <ambient>1.0 0.3 0.0 1</ambient> <!-- 주황색 안전 콘 -->
            <diffuse>1.0 0.3 0.0 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

  </world>
</sdf>
```

---

### 3.2. [Step 3.2] Hunter Gazebo Launch 파일에 `parking_garage.world` 연동

`launch_sim.launch.py` 런치 파일이 기본적으로 신규 `parking_garage.world`를 로드하도록 파라미터 기본값을 업데이트합니다. (기존 파일 수정)

* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/launch_sim.launch.py`

#### 📌 변경 사항 요약 (삭제 `-` 및 추가 `+` 구분)

```diff
  # 2. parking_garage.world 파일 경로 지정
+ world_file_path = os.path.join(
+     get_package_share_directory('hunter_gazebo'), 'worlds', 'parking_garage.world'
+ )
  gazebo_params_file = os.path.join(
      get_package_share_directory('hunter_gazebo'), 'config', 'gazebo_params.yaml'
  )

  # 3. Gazebo Launch (world 파라미터 전달)
  gazebo = IncludeLaunchDescription(
      PythonLaunchDescriptionSource([os.path.join(
          get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py'
      )]),
-     launch_arguments={'extra_gazebo_args': '--ros-args --params-file ' + gazebo_params_file}.items()
+     launch_arguments={
+         'world': world_file_path,
+         'extra_gazebo_args': '--ros-args --params-file ' + gazebo_params_file
+     }.items()
  )

  # 4. AgileX Hunter 로봇 스폰 (주차장 입구 스폰)
  spawn_entity = Node(
      package='gazebo_ros', executable='spawn_entity.py',
      arguments=['-topic', 'robot_description',
                 '-entity', 'hunter_gazebo',
-                '-z', '0.25'],
+                '-x', '0.0', '-y', '-8.0', '-z', '0.25'],
      output='screen'
  )
```

#### 📄 수정 완료된 전체 `launch_sim.launch.py` 코드

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Robot State Publisher 런치
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('hunter_description'), 'launch', 'rsp.launch.py'
        )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    # 2. parking_garage.world 파일 경로 지정
    world_file_path = os.path.join(
        get_package_share_directory('hunter_gazebo'), 'worlds', 'parking_garage.world'
    )
    gazebo_params_file = os.path.join(
        get_package_share_directory('hunter_gazebo'), 'config', 'gazebo_params.yaml'
    )

    # 3. Gazebo Launch (world 파라미터 전달)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py'
        )]),
        launch_arguments={
            'world': world_file_path,
            'extra_gazebo_args': '--ros-args --params-file ' + gazebo_params_file
        }.items()
    )

    # 4. AgileX Hunter 로봇 스폰 (주차장 입구 스폰)
    spawn_entity = Node(
        package='gazebo_ros', executable='spawn_entity.py',
        arguments=['-topic', 'robot_description',
                   '-entity', 'hunter_gazebo',
                   '-x', '0.0', '-y', '-8.0', '-z', '0.25'],
        output='screen'
    )

    diff_drive_spawner = Node(
        package="controller_manager", executable="spawner",
        arguments=["diff_drive_controller"]
    )
    joint_broad_spawner = Node(
        package="controller_manager", executable="spawner",
        arguments=["joint_state_broadcaster"]
    )

    return LaunchDescription([
        rsp,
        gazebo,
        spawn_entity,
        diff_drive_spawner,
        joint_broad_spawner
    ])
```

---

### 3.3. [Step 3.3] `hunter_gazebo/CMakeLists.txt`에 `worlds` 디렉터리 Install 규칙 추가

`colcon build` 실행 시 신규 생성한 `parking_garage.world` 파일이 패키지 설치 경로(`install/`)로 정상 복사되도록 `CMakeLists.txt` 파일의 install 디렉터리 목록에 `worlds`를 추가합니다.

* **파일 위치:** `ros2_ws/src/hunter_robot/hunter_gazebo/CMakeLists.txt`

#### 📌 변경 사항 요약 (삭제 `-` 및 추가 `+` 구분)

```diff
  install(
-   DIRECTORY config launch
+   DIRECTORY config launch worlds
    DESTINATION share/${PROJECT_NAME}
  )
```

#### 📄 수정 완료된 전체 `CMakeLists.txt` 코드

```cmake
cmake_minimum_required(VERSION 3.8)
project(hunter_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
endif()

install(
  DIRECTORY config launch worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
```

---

### 3.4. [Step 3.4] 주차장 월드 스폰 및 센서 토픽/시각화 모니터링

```bash
cd ~/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws
colcon build
source install/setup.bash

# 1. 주차장 월드 환경으로 Gazebo 시뮬레이션 구동
ros2 launch hunter_gazebo launch_sim.launch.py

# 2. 새 터미널에서 RViz2 실행 및 센서 화면 시각화 확인
rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz
```

---

### 3.5. [Step 3.5] teleop 키보드 수동 주행 및 주차선/장애물 반응 테스트

```bash
# 별도 터미널에서 키보드 수동 조종 노드 실행
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
* **검증:** 키보드로 차량을 운전하여 주차 구획선 내로 진입하거나, 기둥/벽면 장애물에 다가갈 때 RViz2 화면의 3D-LiDAR 포인트 클라우드(`/points_raw`) 및 전방 카메라 영상 스트림(`/camera/image_raw`) 상에 장애물 형상이 왜곡 없이 나타나는지 검증합니다.

---

## 4. 검증 체크리스트 (Verification Checklist)

| 번호 | 검증 항목 | 검증 방법 및 기준 | 통과 여부 |
|:---:|:---|:---|:---:|
| 1 | **World 스폰** | Gazebo 상에 외벽(입구 포함), AgileX 맞춤 흰색 주차선, 기둥, 주차 장애물이 에러 없이 로드됨 | [ ] |
| 2 | **로봇 스폰 위치** | AgileX Hunter 로봇이 주차장 입구 부근`(0, -8, 0.25)`에 바퀴 떠받침 없이 정상 스폰됨 | [ ] |
| 3 | **3D-LiDAR 인식** | 3D-LiDAR 레이저 포인트 클라우드가 기둥, 벽면, 주차 장애물 차량의 윤곽을 정확히 반사함 | [ ] |
| 4 | **카메라 렌더링** | 전방 카메라 화면에 흰색 주차선, 주황색 라바콘, 파란색/은색 장애물 차량 형상이 정상 렌더링됨 | [ ] |
| 5 | **물리 충돌** | 기둥/벽/장애물 차량 충돌 시 통과하지 않고 정지하며 `/odom` 오도메트리 데이터가 정상 업데이트됨 | [ ] |

---

## 5. 트러블슈팅 (Troubleshooting & Known Issues)

* **문제 1: `colcon build` 후 `parking_garage.world` 파일을 찾을 수 없는 오류**
  - **원인:** `hunter_gazebo/CMakeLists.txt` 파일에 `worlds` 디렉터리 install 규칙이 누락됨
  - **해결:** `hunter_gazebo/CMakeLists.txt` 파일 내 `install(DIRECTORY config launch worlds DESTINATION share/${PROJECT_NAME})` 구문 수정 및 추가

* **문제 2: 주차선(White Lines)이 지면 메쉬 아래로 사라지거나 깜빡거리는 현상 (Z-fighting)**
  - **원인:** 지면 plane`(Z=0)`과 주차선 visual의 높이 차이가 없거나 너무 미세함
  - **해결:** SDF 파일 내 주차선 pose Z값을 `0.002m`로 고정하여 반사 및 시각화 품질 확보
