# ROS2 Hunter Robot 생성 및 수정 파일 이력 (Log)

본 문서는 `ros2_ws/src/hunter_robot` 리포지토리를 클론한 이후, 프로젝트 진행 과정에서 새로 생성된 파일과 수정(커스텀)된 파일의 상대 경로 및 내역 목록입니다.

---

### 1. 🆕 새로 생성한 파일 (Newly Created Files)

1. **sensors.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/sensors.xacro`
   * **설명:** 3D-LiDAR(Velodyne) `/scan` 및 전방 카메라 `/camera/image_raw` URDF 링크 및 Gazebo 센서 플러그인 정의 (Step 02)

2. **parking_garage.world**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/worlds/parking_garage.world`
   * **설명:** 외벽, 기둥 4개, 주차 구획선, 장애물이 포함된 전용 가상 주차장 시뮬레이션 월드 SDF 파일 (Step 03)

3. **mapper_params_online_async.yaml**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/mapper_params_online_async.yaml`
   * **설명:** `slam_toolbox` 연동을 위한 SLAM 파라미터 설정 파일 (센서 토픽 `/scan`, 프레임 `base_link`, `odom`, `map` 및 CeresSolver 설정) (Step 04)

4. **slam_mapping.launch.py**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/slam_mapping.launch.py`
   * **설명:** Gazebo 주차장 월드 구동과 `slam_toolbox` 노드를 동시에 실행하는 SLAM 통합 런치 스크립트 (Step 04)

5. **ackermann_controllers.yaml**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/ackermann_controllers.yaml`
   * **설명:** Hunter 2.0 물리 제원(축거 0.65m, 윤거 0.57m)을 반영한 아커만 전용 컨트롤러(`ackermann_steering_controller`) 설정 신규 파일 (Step 02/Step 04)

---

### 2. ✏️ 클론 후 수정한 파일 (Modified Files)

1. **hunter.urdf.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/hunter.urdf.xacro`
   * **수정 내용:** `sensors.xacro` 센서 인클루드 구문 추가 (Step 02)

2. **hunter_core.urdf.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/hunter_core.urdf.xacro`
   * **수정 내용:** `base_footprint_joint` 오프셋을 축소된 바퀴 반지름 비율(`wheel_radius * 0.6`)로 보정하여 지면 착지 완벽 동기화 (Step 01, Step 02, Step 04)

3. **wheel.urdf.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/wheel.urdf.xacro`
   * **수정 내용:** 전륜 Z축 조향 관절(`steering_joint`, `limit lower="-1.2" upper="1.2"`) 및 킹핀 링크(`steering_link`) 신규 정의, 감쇄(`damping="1.0"`) 적용, 고정 마찰력 벡터(`fdir1`) 제거 및 수동 바퀴 마찰력(`mu1=0.5, mu2=0.5`) 보정 (Step 01, Step 02, Step 04)

4. **ros2_control.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/ros2_control.xacro`
   * **수정 내용:** 전륜 조향 관절 `position` 인터페이스 선언 및 `libgazebo_ros2_control` 플러그인 내 `/cmd_vel` 자동 연동 리매핑 태그 추가 (Step 02, Step 04)

5. **launch_sim.launch.py**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/launch_sim.launch.py`
   * **수정 내용:** `parking_garage.world` 지정, 시작 위치`(0, -8, 0.25)` 파라미터 추가 및 `ackermann_steering_controller` 스포너 노드 적용 (Step 01, Step 02, Step 03, Step 04)

6. **rsp.launch.py**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/launch/rsp.launch.py`
   * **수정 내용:** Xacro 생성 XML 주석 내 `--` 문자로 인한 `gazebo_ros2_control` rcl 파서 에러 예방용 주석 제거 로직 추가 (Step 02, Step 04)

7. **view_hunter.rviz**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/view_hunter.rviz`
   * **수정 내용:** LiDAR PointCloud 및 Camera Image 시각화 디스플레이 설정 업데이트 (Step 02, Step 03)

8. **CMakeLists.txt**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/CMakeLists.txt`
   * **수정 내용:** 빌드 시 `worlds` 및 `maps` 디렉토리가 포함되어 설치되도록 `install(DIRECTORY config launch worlds maps DESTINATION share/${PROJECT_NAME})` 타겟 수정 (Step 03, Step 04)

---

### 3. 📦 원본 클론 유지 디렉토리 (Original Cloned Directories)

* `ros2_ws/src/hunter_robot/hunter_base/`
* `ros2_ws/src/hunter_robot/hunter_controller/`
* `ros2_ws/src/hunter_robot/hunter_description/meshes/`
