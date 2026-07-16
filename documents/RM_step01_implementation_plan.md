# 1단계: 개발 환경 구축 및 로봇 센서 데이터 검증

## 목표
- `linorobot2` 관련 패키지의 의존성을 설치하고, ROS 2 워크스페이스를 빌드합니다.
- Gazebo 시뮬레이터에서 로봇 모델을 구동하여 3D-LiDAR 및 카메라 센서 데이터가 정상적으로 발행(Publish)되는지 검증합니다.

## 제안된 변경 사항
이 단계에서는 소스 코드 파일의 직접적인 변경보다는 개발 환경 설치 및 검증 명령어 실행이 중심입니다.

### [ROS2 Workspace]
#### [MODIFY] [package.xml](file:///home/USER/USER_ws/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/linorobot2/linorobot2_gazebo/package.xml)
- 이미 `python3-collada` 및 `python3-opencv` 의존성이 추가되어 있는 것을 확인했습니다. 추가적인 수정은 필요하지 않습니다.

---

## 검증 계획

### 의존성 설치 및 빌드
Ubuntu 22.04 LTS 환경 내에서 아래 명령을 순서대로 실행합니다:
1. **패키지 업데이트 및 pip 설치:**
   ```bash
   sudo apt update
   sudo apt install -y python3-pip
   ```
2. **의존성(rosdep) 설치:**
   ```bash
   cd ~/USER_ws/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws
   rosdep update
   rosdep install --from-path src --ignore-src -y --skip-keys microxrcedds_agent --skip-keys micro_ros_agent --skip-keys python3-opencv-contrib-python --skip-keys python3-pycollada
   ```
3. **워크스페이스 빌드:**
   ```bash
   colcon build
   source install/setup.bash
   ```

### Gazebo 시뮬레이션 및 센서 데이터 검증
1. **시뮬레이션 구동:**
   - Gazebo에서 `linorobot2` 로봇과 월드를 띄웁니다.
   - 예시 실행 명령어 (로봇 유형에 따라 다름, 4wd/2wd 등 설정 필요):
     ```bash
     export LINOROBOT2_BASE=2wd
     ros2 launch linorobot2_gazebo gazebo.launch.py
     ```
2. **센서 토픽 모니터링:**
   - 터미널을 새로 열어 `/scan` 및 `/camera/image_raw` 등의 토픽이 정상 수신되는지 확인합니다:
     ```bash
     ros2 topic hz /scan
     ros2 topic hz /camera/image_raw
     ```
3. **키보드 수동 주행 및 오도메트리 검증:**
   - `teleop_twist_keyboard`를 실행해 차량을 움직이며 `/odom` 데이터 변화를 모니터링합니다:
     ```bash
     ros2 run teleop_twist_keyboard teleop_twist_keyboard
     ```
