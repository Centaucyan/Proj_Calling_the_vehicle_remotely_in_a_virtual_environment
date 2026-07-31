# Proj_Calling_the_vehicle_remotely_in_a_simulation_env

* Update: 2026.07.29.(프로젝트 4/10 단계 진행 중)
## 1. Description
* 시뮬레이션 환경에서 리모컨(Qt Dashborad)으로 차량을 호출하면, 차량은 리모컨의 위치로 자율 주행 이동.(프로젝트 과정은 '/documents/RM_Step01-10_*.md'에 정리하며 진행)
* **Github Repository:** https://github.com/Centaucyan/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment.git
* **Vehicle model:** AgileX Hunter
* **Tool:**
  * slam-toolbox
  * nav2-map-server

![Gazebo](./documents/images/hunter_in_gazebo.png)
![Rviz2](./documents/images/hunter_in_rviz2.png)
---

## 2. Environment
* **OS:** Ubuntu 22.04 LTS(Jammy Jellyfish)
* **Language:** C++, Python(Ver: 3.10)
* **Middle ware:** ROS 2 Humble Hawksbill
* **Simulator:** Gazebo
* **Visualization Tool:** RViz2
---

## 3. 저장소 클론 및 서브모듈(Submodule) 다운로드 가이드

다른 PC나 새로운 개발 환경에서 이 저장소를 클론할 때 외부 의존성 서브모듈(`ros2_ws/src/hunter_ros2` 등)을 함께 내려받는 2가지 방법.

### 3.1. [방법 1] 저장소 클론 시 서브모듈 한 번에 내려받기 (추천 🌟)
`--recurse-submodules` 옵션을 사용하면 메인 저장소와 연결된 모든 서브모듈을 한 번에 자동으로 클론함.

```bash
git clone --recurse-submodules https://github.com/Centaucyan/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment.git
cd Proj_Calling_the_vehicle_remotely_in_a_virtual_environment
```

### 3.2. [방법 2] 일반 `git clone` 후 서브모듈 별도 동기화하기
이미 `git clone`을 실행했거나 서브모듈이 다운로드되지 않아 폴더가 비어있는 경우 서브모듈을 초기화하고 수동으로 내려받음.

```bash
# 1. 메인 저장소 클론 및 이동
git clone https://github.com/Centaucyan/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment.git
cd Proj_Calling_the_vehicle_remotely_in_a_virtual_environment

# 2. 서브모듈 초기화 및 동기화 다운로드
git submodule update --init --recursive
```
---

## 4. Pre-installation
* $ sudo apt update && sudo apt upgrade
* $ sudo apt install -y \
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
  ros-humble-slam-toolbox \
  ros-humble-nav2-map-server \
  ros-humble-pointcloud-to-laserscan \
  ros-humble-ackermann-steering-controller \
  ros-humble-ackermann-msgs \
  ros-humble-steering-controllers-library
---

## 5. Execute Commands
```bash
# 1. ros2_ws 이동
cd Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws

# 2. 의존성 패키지 설치(git clone 후 처음에만 실행)
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# 3. ros packages build
colcon build

# 4. Gazebo 시뮬레이션 스폰 (3D-LiDAR & 카메라 통합 로봇)
source install/setup.bash
ros2 launch hunter_gazebo launch_sim.launch.py

# 5. 새 터미널에서 RViz2 구동 및 센서 시각화 확인
source install/setup.bash
rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz

# 6. 새 터미널에서 키보드 노드 실행 및 차량 조작
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## 6. Reference
* **Github Repository:** 
  * https://github.com/LCAS/hunter_robot.git
  * https://github.com/agilexrobotics/ugv_sdk.git
---

## 7. ROS2 노드 구성도 (아키텍처)
![Node Architecture](./documents/images/ROS2_node_structure.png)
---