# Proj_Calling_the_vehicle_remotely_in_a_simulation_env

* Update: 2026.08.04.(프로젝트 5/10 단계 완료)
* Project duration: 2026.07.15 ~
## 1. Description
* 시뮬레이션 환경에서 리모컨(Qt Dashborad)으로 차량을 호출하면, 차량은 리모컨의 위치로 자율 주행 이동.(프로젝트 과정은 '/documents/development_process/RM_Step01-10_*.md'에 정리하며 진행)
* **목적:** 테슬라 Smart Summon 기능을 가상 환경에서 구현해봄으로써 SLAM(지도 작성)과 NAV2(경로 계획, 장애물 회피)를 경험 및 이해
* **Github Repository:** https://github.com/Centaucyan/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment.git
* **Vehicle model:** AgileX Hunter(기본 설정인 Differential Drive 방식을 Ackermann Steering 방식으로 변경 사용)
* **Tool:**
  * 지도 작성
    * slam-toolbox
    * nav2-map-server
  * Navigation
    * navigation2
    * nav2-bringup
    
![Autonomous Navigation](./documents/videos/autonomous_navigation_01.gif)
---

## 2. DFD(Data Flow Diagram)
![Node Architecture](./documents/images/data_flow_diagram.png)
---

## 3. Environment
* **OS:** `Ubuntu 22.04 LTS(Jammy Jellyfish)`
* **Language:** `C++, Python(Ver: 3.10)`
* **Middle ware:** `ROS 2 Humble Hawksbill`
* **Simulator:** `Gazebo`
* **Visualization Tool:** `RViz2`
* **경로 계획 알고리즘 (Global Planner):** `Hybrid-A*`
  - **개요**: 기존 A* 알고리즘의 한계(격자 지도 기반의 각진 경로)를 보완하여, 차량이 주행 가능한 곡선 궤적을 반영해 탐색.
  - **곡선 모션 모델 (`Reeds-Shepp`)**: 전진과 후진을 모두 고려한 곡선을 생성하여 좁은 공간이나 코너에서도 탈출 경로 계획 가능. *(참고: 전진 전용은 Dubins 모델)*
---

## 4. 저장소 클론 및 서브모듈(Submodule) 다운로드 가이드

다른 PC나 새로운 개발 환경에서 이 저장소를 클론할 때 외부 의존성 서브모듈(`ros2_ws/src/hunter_ros2` 등)을 함께 내려받는 2가지 방법.

### 4.1. [방법 1] 저장소 클론 시 서브모듈 한 번에 내려받기 (추천 🌟)
`--recurse-submodules` 옵션을 사용하면 메인 저장소와 연결된 모든 서브모듈을 한 번에 자동으로 클론함.

```bash
git clone --recurse-submodules https://github.com/Centaucyan/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment.git
cd Proj_Calling_the_vehicle_remotely_in_a_virtual_environment
```

### 4.2. [방법 2] 일반 `git clone` 후 서브모듈 별도 동기화하기
이미 `git clone`을 실행했거나 서브모듈이 다운로드되지 않아 폴더가 비어있는 경우 서브모듈을 초기화하고 수동으로 내려받음.

```bash
# 1. 메인 저장소 클론 및 이동
git clone https://github.com/Centaucyan/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment.git
cd Proj_Calling_the_vehicle_remotely_in_a_virtual_environment

# 2. 서브모듈 초기화 및 동기화 다운로드
git submodule update --init --recursive
```
---

## 5. Pre-installation

본 프로젝트 실행에 필요한 ROS 2 Humble 및 시뮬레이션 의존성 패키지 일괄 설치 명령과 주요 패키지별 상세 역할 구분입니다.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  libasio-dev \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-gazebo-ros2-control \
  ros-humble-teleop-twist-keyboard \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-xacro \
  ros-humble-gazebo-plugins \
  ros-humble-velodyne-description \
  ros-humble-image-transport-plugins \
  ros-humble-rviz2 \
  ros-humble-ackermann-steering-controller \
  ros-humble-ackermann-msgs \
  ros-humble-steering-controllers-library \
  ros-humble-slam-toolbox \
  ros-humble-nav2-map-server \
  ros-humble-pointcloud-to-laserscan \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup
```

### 📦 사전 설치 의존성 패키지 상세 개별 목록

| 분류 | 패키지명 | 역할 및 상세 설명 |
| :--- | :--- | :--- |
| **C++ SDK & 통신** | `libasio-dev` | C++ 비동기 네트워크/시리얼/CAN 통신 범용 개발 라이브러리 (AgileX `ugv_sdk` 통신 모듈 컴파일 시 사용) |
| **시뮬레이션 & 기본 제어** | `ros-humble-gazebo-ros-pkgs` | Gazebo 물리 시뮬레이터와 ROS 2 간의 클록, 모델 스폰, 관절 상태 통신 전용 인터페이스 패키지 모음 |
| | `ros-humble-ros2-control` | 로봇 하드웨어와 제어 알고리즘(Controller) 간의 입출력을 총괄 관리하는 ROS 2 표준 제어 프레임워크 |
| | `ros-humble-ros2-controllers` | 관절 상태 브로드캐스터, 위치/속도 제어기 등 표준 로봇 제어기 구현체 라이브러리 모음 |
| | `ros-humble-gazebo-ros2-control` | Gazebo 가상 로봇에 `ros2_control` 제어기를 결합하여 시뮬레이션 모터를 구동하는 전용 플러그인 |
| | `ros-humble-teleop-twist-keyboard` | 키보드 입력을 기반으로 로봇의 이동 속도 명령(`/cmd_vel`)을 퍼블리시하는 수동 조작 노드 |
| | `ros-humble-joint-state-publisher` | 로봇 URDF 각 관절 상태를 수집하고 `/joint_states` 토픽으로 트래킹하는 노드 |
| | `ros-humble-joint-state-publisher-gui` | GUI 인터페이스의 슬라이더를 통해 관절 각도를 수동으로 조작해 볼 수 있는 도구 |
| | `ros-humble-xacro` | 복잡한 로봇 3D/URDF 구조를 매크로, 변수, 파일 분할을 통해 효율적으로 해석하는 XML 파서 툴 |
| **센서 & 차량 조향** | `ros-humble-gazebo-plugins` | Gazebo 가상 환경 내 센서(카메라, LiDAR, IMU 등) 렌더링 및 ROS 2 토픽 수송 공식 플러그인 모음 |
| | `ros-humble-velodyne-description` | Velodyne 3D-LiDAR 센서(VLP-16 등)의 3D 메쉬 파일 및 URDF 링크 정의 패키지 |
| | `ros-humble-image-transport-plugins` | 카메라 영상 데이터(Raw Image)를 압축 전송하여 네트워크 대역폭을 절약하는 플러그인 모음 |
| | `ros-humble-rviz2` | 3D 센서 포인트클라우드, 로봇 3D 모델, TF 좌표계 및 2D/3D 지도를 실시간 관찰하는 시각화 도구 |
| | `ros-humble-ackermann-steering-controller` | 아커만 조향 구조(전륜 조향-후륜 구동) 차량용 ROS 2 범용 아커만 조향 제어기 플러그인 |
| | `ros-humble-ackermann-msgs` | 아커만 조향 제어 데이터 규격(`ackermann_msgs/msg/AckermannDrive`)을 정의하는 전용 메시지 패키지 |
| | `ros-humble-steering-controllers-library` | 조향 기반 차량 제어기의 공통 역동학 계산 및 궤적 수송을 다루는 하위 C++ 라이브러리 |
| **2D SLAM 매핑** | `ros-humble-slam-toolbox` | 2D 점유 격자 지도 구축, 그래프 최적화(Ceres Solver) 및 루프 클로저를 수행하는 SLAM 패키지 |
| | `ros-humble-nav2-map-server` | 완성된 지도를 정적 파일(`map.yaml`, `.pgm`)로 저장하는 CLI 도구(`map_saver_cli`) 및 맵 서버 패키지 |
| | `ros-humble-pointcloud-to-laserscan` | 3D LiDAR 포인트클라우드(`/points_raw`)를 2D SLAM용 레이저스캔(`/scan`) 토픽으로 실시간 가공/변환 |
| **Nav2 자율주행** | `ros-humble-navigation2` | 전역/지역 경로 계획(Planner/Controller), 비용 지도(Costmap), AMCL 위치추정 및 BT Navigator 핵심 스택 |
| | `ros-humble-nav2-bringup` | Nav2 프레임워크의 여러 노드를 한 번에 구동하고 관리하는 공식 Bringup 런치 스크립트 및 템플릿 |
---

## 6. Create the 2d-map(지도 생성 필요 시)
```bash
# 1. ros2_ws 이동
cd Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws

# 2. [터미널 1] SLAM 통합 런치 실행
source install/setup.bash
ros2 launch hunter_gazebo slam_mapping.launch.py

# 3. [터미널 2] RViz2 구동 및 실시간 2D 지도 시각화
source install/setup.bash
rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz

# 4. [터미널 3] 키보드 제어로 주차장 전체 구역 조종 주행
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 5. [터미널 4] 완성된 2D 지도 저장 (주행 완료 후)
source install/setup.bash
ros2 run nav2_map_server map_saver_cli -f src/hunter_robot/hunter_gazebo/maps/parking_garage_map
```
---

## 7. Execute Commands
```bash
# 1. ros2_ws 이동
cd Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws

# 2. 의존성 패키지 설치(git clone 후 처음에만 실행)
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# 3. ROS Packages build
colcon build

# 4. Gazebo 시뮬레이션 스폰 (3D-LiDAR & 카메라 통합 로봇)
source install/setup.bash
ros2 launch hunter_gazebo bringup_sim_nav2.launch.py

# 5. 새 터미널에서 RViz2 구동: 센서 시각화 및 2D Pose Estimate(차량 첫 위치 및 방향 설정), 2D Goal Pose(차량 최종 위치 및 방향 설정) 버튼으로 자율 주행 구현_(본 문서 '1. Description' 영상 참조)
source install/setup.bash
rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz
  ** PC 성능에 따라 RViz2가 실행 된 후 2d_map이 loading 되는 시간이 길수도 있음.

  Option) 자율주행 상태 및 결과 실시간 모니터링
  ros2 topic echo /navigate_to_pose/_action/status

  ** 출력 상태 코드(Status)의 의미 **
    - `status: 2`: 목표를 향해 열심히 자율주행 진행 중 (Executing)
    - `status: 4`: 목적지(XY 및 회전 오차 범위 내) 무사 도착 완료 (Succeeded)
    - `status: 5`: 사용자나 시스템에 의해 주행 취소됨 (Canceled)
    - `status: 6`: 코너에 갇히거나 경로를 찾을 수 없어 주행 포기 (Aborted/Failed)

# 6. 새 터미널에서 키보드 노드 실행 및 차량 수동 조작
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
---

## 8. Reference
* **Github Repository:** 
  * https://github.com/LCAS/hunter_robot.git
  * https://github.com/agilexrobotics/ugv_sdk.git
* **Document Site:** 
  * https://wiki.ros.org/slam_toolbox/
  * https://index.ros.org/p/nav2_map_server/
  * https://docs.nav2.org/index.html
  * https://index.ros.org/p/nav2_bringup/
  * https://control.ros.org/humble/index.html/
---