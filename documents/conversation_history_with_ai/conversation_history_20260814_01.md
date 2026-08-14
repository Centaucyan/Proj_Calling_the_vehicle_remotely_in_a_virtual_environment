# 2026년 08월 14일 대화 기록 및 학습 내역 (Conversation & Study History)

**작성일시:** 2026-08-14
**프로젝트명:** Vision AI 기반 자율주행 모형 차량 원격 호출 및 정밀 주차 시뮬레이션 시스템
---

## 📌 1. 프로젝트 전체 진행 상황 검토 (Status Review)

* **진행도:** 총 10단계 개발 로드맵 중 **5단계 완료 (50% 달성)**
* **완료된 단계 (Step 01 ~ Step 05):**
  - **Step 01:** 개발 환경 구축, AgileX Hunter 기본 모델 Gazebo 스폰 및 키보드 조작 검증
  - **Step 02:** URDF 3D-LiDAR/카메라 센서 결합, 아커만 조향 동역학 튜닝, 지면 오프셋 및 바퀴 슬립 방지 마찰력(`mu1=100`, `mu2=100`) 적용
  - **Step 03:** 가상 주차장 시뮬레이션 월드(`parking_garage.world`) 제작 및 로봇 스폰
  - **Step 04:** `slam_toolbox` 기반 수동 매핑 및 정적 2D 점유 격자 지도(`parking_garage_map.yaml`, `.pgm`) 작성 완료
  - **Step 05:** **ROS 2 Nav2 자율주행 프레임워크 완성**
    - 3D LiDAR 포인트클라우드를 2D LaserScan(`/scan`)으로 실시간 변환 (`pointcloud_to_laserscan`)
    - AMCL 위치 추정 및 Global/Local Costmap 구축
    - 전역 플래너: `SmacPlannerHybrid` (최소 회전반경 1.6m 아커만 궤적 지원)로 제자리 회전(Spin) 에러 해결
    - 지역 제어기: `RegulatedPurePursuitController` (`use_rotate_to_heading: false`, 후진 `allow_reversing: true`)
    - 통합 런치 스크립트 (`bringup_sim_nav2.launch.py`) 완성
* **향후 예정 단계 (Step 06 ~ Step 10):**
  - Step 06: Qt 대시보드 UI 및 시스템 매니저 FSM 연동 (`qt_dashboard_node`, `system_manager_node`)
  - Step 07: Vision AI (YOLO 등) 객체 인지 모듈 개발 (`vision_ai_node`)
  - Step 08: 3D LiDAR + Vision AI 융합 기반 고립 감지 및 비상 정지 (`obstacle_avoidance_helper_node`)
  - Step 09: 강화학습(RL) 기반 호출기 반경 1m 내 10cm 오차 초정밀 밀착 주차 (`rl_parking_node`)
  - Step 10: 전체 시나리오(TC1~TC3) 시스템 통합 및 종합 검증

---

## 📌 2. 핵심 질의응답 (Q&A) 및 아키텍처 학습 내역

### Q1. Step 01에서 `launch_sim.launch.py`를 실행할 때 데이터가 어떻게 흘러서 Gazebo에 3D 모델이 나타나는가?

* **데이터 흐름 5단계 Summary:**
  1. **Xacro 파싱:** `rsp.launch.py` 실행 시 `xacro.process_file()`이 `hunter.urdf.xacro` 및 하위 센서/차체 파일들을 단 하나의 XML 문자열 데이터로 만듦.
  2. **라디오 방송:** `robot_state_publisher` 노드가 이 XML 데이터를 **`/robot_description`** 토픽으로 실시간 방송함.
  3. **World 생성:** `gazebo.launch.py`가 가제보 3D 물리 엔진(`gzserver`)과 GUI(`gzclient`)를 켜고 `parking_garage.world`를 로드함.
  4. **3D 로봇 스폰:** `spawn_entity.py` 노드가 `/robot_description` 토픽을 수신해 XML 로봇 정보를 얻고, `/spawn_entity` 서비스 통신으로 Gazebo 주차장의 `(x:0.0, y:-8.0, z:0.25)` 위치에 3D 모델을 소환함.
  5. **모터 결합:** `controller_manager` 스포너가 구동 바퀴 및 조향 관절 제어기를 바퀴 모터에 결합함.

---

### Q2. `launch_sim.launch.py`에서 `spawner` 노드를 `ackermann_spawner`와 `joint_broad_spawner`로 2번 실행하는 이유는?

* **이유:** ROS 2 `ros2_control` 프레임워크에서 `spawner`는 컨트롤러를 로드/활성화하는 유틸리티이며, 역할이 완전히 다른 2개 컨트롤러가 필요하기 때문.
  - **`ackermann_spawner` (`ackermann_steering_controller`):** `/cmd_vel` 명령(속도, 조향각)을 수신해 실제 가제보 로봇 바퀴 속도와 조향 모터를 조종하고 오도메트리(`/odom`)를 발행하는 **주행 운전기사** 역할.
  - **`joint_broad_spawner` (`joint_state_broadcaster`):** 로봇 바퀴 회전각과 조향각 위치를 실시간 읽어와 **`/joint_states`** 토픽으로 쏘아주어, TF 좌표계 계산 및 RViz2/Gazebo 3D 시각화를 가능하게 하는 **상태 리포터** 역할.

---

### Q3. `spawner` 노드 소스 코드 안에 `ackermann_steering_controller` 같은 함수가 직접 작성되어 있는가?

* **답변:** **아니다.**
* **작동 원리:**
  - `spawner`는 단지 서비스 요청(`/controller_manager/load_controller`)을 전송하는 메신저(CLI 도구)일 뿐임.
  - `ackermann_steering_controller`는 시스템에 사전 빌드/설치된 독립적인 **C++ 동적 공유 라이브러리(`.so` 파일, C++ Pluginlib)**임.
  - `spawner`가 요청을 보내면, Gazebo 내부에서 구동 중인 `controller_manager` 노드가 `ackermann_controllers.yaml` 설정 파일에서 `type: ackermann_steering_controller/AckermannSteeringController` 정보를 확인하고, C++ 동적 라이브러리(`libackermann_steering_controller.so`)를 메모리에 불러와(`dlopen`) 클래스 객체를 생성함.

---

### Q4. `controller_manager` 노드가 `ackermann_controllers.yaml` 파일 경로를 알아내도록 명령하는 코드는 어디에 있는가?

* **정답 코드 위치:** `ros2_ws/src/hunter_robot/hunter_description/description/ros2_control.xacro`
* **코드 내용:**
  ```xml
  <gazebo>
      <plugin name="gazebo_ros2_control_hunter" filename="libgazebo_ros2_control.so">
          <!-- 🌟 바로 이 줄에서 파라미터 YAML 파일 경로를 지정함 -->
          <parameters>$(find hunter_gazebo)/config/ackermann_controllers.yaml</parameters>
          <ros>
              <remapping>/ackermann_steering_controller/reference_unstamped:=/cmd_vel</remapping>
              <remapping>/ackermann_steering_controller/tf_odometry:=/tf</remapping>
          </ros>
      </plugin>
  </gazebo>
  ```
* **설명:** 로봇 URDF 파일 안의 `<plugin filename="libgazebo_ros2_control.so">` 태그 안에 `<parameters>`로 YAML 파일 경로가 명시되어 있어, 로봇이 Gazebo에 스폰되는 순간 해당 파라미터 장부를 읽어 들이게 됨.

---

### Q5. `ros2 launch hunter_gazebo bringup_sim_nav2.launch.py` 실행 시 백그라운드에서 어떤 일이 일어나는가?

* **마스터 통합 런치 구동 3단계:**
  1. **`launch_sim.launch.py`:** Xacro 파싱 ➡️ Gazebo 월드 렌더링 ➡️ 주차장 입구에 3D Hunter 로봇 소환 ➡️ 모터 제어기 결합 ➡️ 3D LiDAR `/points_raw` 데이터 분출 시작.
  2. **`pointcloud_to_laserscan_node`:** 3D LiDAR 포인트클라우드(`/points_raw`)를 받아서 Z축 필터링(`min_height: -0.1`, `max_height: 1.0`) 후, 2D 자율주행 입력 데이터인 `/scan` (`sensor_msgs/msg/LaserScan`)으로 실시간 변환.
  3. **`navigation.launch.py` (Nav2 두뇌 스택):** 
     - `map_server`: `parking_garage_map.yaml` 지도를 `/map` 토픽으로 전송.
     - `amcl`: 레이저 센서 데이터와 오도메트리를 비교하여 로봇 위치 추정 파티클 수렴 시작.
     - `planner_server`: `SmacPlannerHybrid` 플래너 준비 (최소 회전반경 1.6m 아커만 전역 경로 생성 대기).
     - `controller_server`: `RegulatedPurePursuitController` 제어기 준비 (조향 및 속도 명령 `/cmd_vel` 계산 대기).
     - `behavior_server` & `bt_navigator`: 비상 복구 행동 및 행동 트리 의사결정 준비.
     - `lifecycle_manager_navigation`: 위 6개 노드를 `Active` 상태로 일괄 전환하여 자율주행 명령 수신 대기 상태로 정립.

---

### Q6. `launch_sim.launch.py`의 `os.path.join(get_package_share_directory('gazebo_ros'), ...)`에서 `gazebo_ros` 폴더 위치와 `get_package_share_directory()`의 역할은?

1. **`gazebo_ros` 폴더 위치:**
   - 시스템 설치 ROS 2 공식 패키지의 share 경로인 `/opt/ros/humble/share/gazebo_ros/`에 위치함.
   - 그 하위에 `launch/gazebo.launch.py` 스크립트가 존재함.
2. **`get_package_share_directory()` 함수의 역할:**
   - 개발자 컴퓨터 환경이나 사용자 계정 이름이 달라도, ROS 2 환경변수(`AMENT_PREFIX_PATH`)를 탐색하여 특정 패키지의 `share` 디렉토리 **절대 경로(Absolute Path)**를 자동으로 반환해 주는 함수.
   - 이로 인해 경로 하드코딩 없이 어떤 PC에서나 포터블하게 런치 파일이 구동됨.

---
