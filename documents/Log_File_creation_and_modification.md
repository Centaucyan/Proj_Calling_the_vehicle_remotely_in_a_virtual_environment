# ROS2 Hunter Robot 생성 및 수정 파일 이력 (Log)

본 문서는 `ros2_ws/src/hunter_robot` 리포지토리를 클론한 이후, 프로젝트 진행 과정에서 새로 생성된 파일과 수정(커스텀)된 파일의 상대 경로 및 내역 목록입니다.

---

### 1. 🆕 새로 생성한 파일 (Newly Created Files)

1. **[sensors.xacro]**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/sensors.xacro`
   * **설명:** 3D-LiDAR(Velodyne) `/scan` 및 전방 카메라 `/camera/image_raw` URDF 링크 및 Gazebo 센서 플러그인 정의

2. **[parking_garage.world]**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/worlds/parking_garage.world`
   * **설명:** 외벽, 기둥 4개, 주차 구획선, 장애물이 포함된 전용 가상 주차장 시뮬레이션 월드 SDF 파일

---

### 2. ✏️ 클론 후 수정한 파일 (Modified Files)

1. **hunter.urdf.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/hunter.urdf.xacro`
   * **수정 내용:** `sensors.xacro` 센서 인클루드 구문 추가

2. **hunter_core.urdf.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/hunter_core.urdf.xacro`
   * **수정 내용:** 차체 지상고 오프셋 및 오도메트리 파라미터 미세 조정

3. **wheel.urdf.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/wheel.urdf.xacro`
   * **수정 내용:** 바퀴 접지 위치 및 조향 축 오프셋 조정

4. **launch_sim.launch.py**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/launch_sim.launch.py`
   * **수정 내용:** `parking_garage.world` 지정 및 차량 시작 위치`(0, -8, 0.25)` 파라미터 추가

5. **view_hunter.rviz**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/view_hunter.rviz`
   * **수정 내용:** LiDAR PointCloud 및 Camera Image 시각화 디스플레이 설정 업데이트

6. **CMakeLists.txt**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/CMakeLists.txt`
   * **수정 내용:** 빌드 시 `worlds` 폴더가 복사되도록 `install(DIRECTORY config launch worlds ...)` 수정

---

### 3. 📦 원본 클론 유지 디렉토리 (Original Cloned Directories)

* `ros2_ws/src/hunter_robot/hunter_base/`
* `ros2_ws/src/hunter_robot/hunter_controller/`
* `ros2_ws/src/hunter_robot/hunter_description/meshes/`
