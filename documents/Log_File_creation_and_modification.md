# ROS2 Hunter Robot 생성 및 수정 파일 이력 (Log)

본 문서는 `ros2_ws/src/hunter_robot` 리포지토리를 클론한 이후, 프로젝트 진행 과정에서 새로 생성된 파일과 수정(커스텀)된 파일의 상대 경로 및 내역 목록입니다.

---

### 1. 🆕 새로 생성한 파일 (Newly Created Files)

1. **sensors.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/sensors.xacro`
   * **설명:** 3D-LiDAR(Velodyne) **`/points_raw`** 및 전방 카메라 `/camera/image_raw` URDF 링크 및 Gazebo 센서 플러그인 정의 (Step 02)

2. **parking_garage.world**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/worlds/parking_garage.world`
   * **설명:** 외벽, 기둥 4개, 주차 구획선, 장애물이 포함된 전용 가상 주차장 시뮬레이션 월드 SDF 파일 (Step 03)

3. **mapper_params_online_async.yaml**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/mapper_params_online_async.yaml`
   * **설명:** `slam_toolbox` 연동을 위한 SLAM 파라미터 설정 파일 (센서 토픽 `/scan`, 프레임 `base_link`, `odom`, `map` 및 CeresSolver 설정) (Step 04)

4. **slam_mapping.launch.py**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/slam_mapping.launch.py`
   * **설명:** Gazebo 주차장 월드 구동과 `slam_toolbox` 노드를 동시에 실행하는 SLAM 통합 런치 스크립트. **바닥 레이저 데이터를 장애물로 오인하지 않도록 `min_height: -0.1` 필터링 적용 완료.** (Step 04)

5. **ackermann_controllers.yaml**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/ackermann_controllers.yaml`
   * **설명:** Hunter 2.0 물리 제원(축거 0.512m, 윤거 0.4908m, 바퀴 0.09906m)을 정밀 반영한 아커만 제어기 설정 파일. **물리적 바퀴 슬립에 의한 오도메트리 왜곡을 막기 위한 `open_loop: true` 설정 및 조향축 고정용 강력한 PID 게인(`p: 100.0, i: 0.0, d: 1.0`) 적용 완료.** (Step 02/Step 04)

6. **nav2_params.yaml**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml`
   * **설명:** Nav2 핵심 파라미터 및 아커만 조향 전용 제어기(`RegulatedPurePursuitController`) 설정 파일. **최신 아커만 주행 최적화를 위해 전역 플래너를 `SmacPlannerHybrid`로 전면 교체하였으며, 제자리 회전 에러(Spin)를 방지하기 위해 관련 복구 행동 파라미터를 업데이트 완료함.** (Step 05, Issue 03)

7. **navigation.launch.py**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/navigation.launch.py`
   * **설명:** Nav2 주요 노드(`map_server`, `amcl`, `behavior_server` 등) 구동 런치 스크립트. **Gazebo 전역 변수명과의 덮어쓰기 충돌 에러를 해결하기 위해 파라미터 변수명을 `nav_params_file`로 교체 적용 완료.** (Step 05)

8. **bringup_sim_nav2.launch.py**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/bringup_sim_nav2.launch.py`
   * **설명:** Gazebo 주차장 월드(로봇 스폰 포함), 3D LiDAR 포인트 클라우드 변환(`pointcloud_to_laserscan`), 그리고 Nav2 통합 런치 파일을 모두 한 번에 묶어서 실행하는 최종 구동 파일 (Step 05)

---

### 2. ✏️ 클론 후 수정한 기존 파일 (Modified Files)

1. **hunter.urdf.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/hunter.urdf.xacro`
   * **수정 내용:** `sensors.xacro` 센서 인클루드 구문 추가 (Step 02)

2. **hunter_core.urdf.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/hunter_core.urdf.xacro`
   * **수정 내용:** `base_footprint_joint` 오프셋을 축소된 바퀴 반지름 비율(`wheel_radius * 0.6`)로 보정하여 지면 착지 완벽 동기화 (Step 01, Step 02, Step 04)

3. **wheel.urdf.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/wheel.urdf.xacro`
   * **수정 내용:** 전륜 Z축 조향 관절(`steering_joint`, `limit lower="-1.2" upper="1.2"`) 및 킹핀 링크(`steering_link`) 신규 정의, 감쇄(`damping="1.0"`) 적용, 고정 마찰력 벡터(`fdir1`) 제거 및 **가제보 바퀴 슬립(미끄러짐) 방지를 위한 강력한 마찰력(`mu1=100.0, mu2=100.0`) 보정 적용 완료.** (Step 01, Step 02, Step 04)

4. **ros2_control.xacro**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/description/ros2_control.xacro`
   * **수정 내용:** 전륜 조향 관절 `position` 인터페이스 선언 및 `libgazebo_ros2_control` 리매핑 태그 추가. **더미 노드 제거 후 RViz2에서 앞바퀴가 보이도록 수동 관절(Passive Joint) `state_interface` 추가 완료.** (Step 02, Step 04)

5. **launch_sim.launch.py**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/launch/launch_sim.launch.py`
   * **수정 내용:** `parking_garage.world` 지정, 시작 위치(0, -8, 0.25) 파라미터 추가 및 `ackermann_steering_controller` 스포너 적용. **가제보 컨트롤러와 충돌하여 TF 트리를 깜빡이게 만들던 더미 노드(`joint_state_publisher`) 주석 처리 완료.** (Step 01, Step 02, Step 03, Step 04)

6. **rsp.launch.py**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_description/launch/rsp.launch.py`
   * **수정 내용:** Xacro 생성 XML 주석 내 `--` 문자로 인한 `gazebo_ros2_control` rcl 파서 에러 예방용 주석 제거 로직 추가 (Step 02, Step 04)

7. **view_hunter.rviz**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/config/view_hunter.rviz`
   * **수정 내용:** LiDAR PointCloud, Camera Image 시각화 디스플레이 추가 및 SLAM용 `Map` 디스플레이 설정 업데이트 (Step 02, Step 03, Step 04)

8. **CMakeLists.txt**
   * **경로:** `ros2_ws/src/hunter_robot/hunter_gazebo/CMakeLists.txt`
   * **수정 내용:** 빌드 시 `worlds` 및 `maps` 디렉토리가 포함되어 설치되도록 타겟 수정 (Step 03, Step 04, Step 05)

---

### 3. 📦 원본 클론 유지 디렉토리 (Original Cloned Directories)

* `ros2_ws/src/hunter_robot/hunter_base/`
* `ros2_ws/src/hunter_robot/hunter_controller/`
* `ros2_ws/src/hunter_robot/hunter_description/meshes/`
