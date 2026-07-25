# ROS2 노드 아키텍처 설계서

이 문서는 **"Vision AI 기반 자율주행 모형 차량 원격 호출 및 정밀 주차 시뮬레이션 시스템"**을 위한 ROS2 노드 구성 및 통신 설계를 다룹니다.

---

## 1. ROS2 노드 구성도 (아키텍처)

아래 다이어그램은 각 노드의 역할과 이들이 주고받는 핵심 토픽(Topic) 통신 관계를 도식화한 것입니다.

![Node Architecture](./images/ROS2_node_structure.png)

---

## 2. 개별 노드 역할 및 통신 상세

### ① `qt_dashboard_node` (C++/Qt)
* **역할:** 사용자가 조작하는 리모컨 버튼 입력 및 차량의 현재 상태(LED 상태, 오디오 알람 상태)를 UI에 갱신합니다.
* **주요 통신:**
  * **Publish:** `/remote_call` (`std_msgs/msg/Empty` 또는 `geometry_msgs/msg/PoseStamped`)
    * 사용자가 호출 버튼을 누르면 차량에게 호출 신호 및 가상 리모컨의 현재 좌표를 전송합니다.
  * **Subscribe:** `/vehicle_status` (`std_msgs/msg/String`)
    * 차량의 현재 주행 상태(대기, 점검 중, 주행 중, 고립됨, 주차 중, 종료 등)를 수신해 UI에 반영합니다.
  * **Subscribe:** `/alert_signal` (`std_msgs/msg/Bool`)
    * 시스템 에러나 고립 시 경보음 작동 신호를 수신합니다.

### ② `system_manager_node` (C++)
* **역할:** 전체 시스템의 라이프사이클과 모드를 제어하는 상태 머신(State Machine) 역할을 합니다.
* **주요 통신:**
  * **Subscribe:** 
    * `/remote_call` (`std_msgs/msg/Empty` 또는 `geometry_msgs/msg/PoseStamped`)
    * `/health_check` (`std_msgs/msg/Bool`)
    * `/path_blocked` (`std_msgs/msg/Bool`)
    * `/parking_status` (`std_msgs/msg/String`)
  * **Publish:**
    * `/vehicle_status` (`std_msgs/msg/String` -> Qt UI용 정보 제공)
    * `/alert_signal` (`std_msgs/msg/Bool` -> Qt UI용 정보 제공)
    * `/goal_pose` (`geometry_msgs/msg/PoseStamped` -> Nav2의 Goal 전달)
    * `/start_parking` (`std_msgs/msg/Bool` -> 강화학습 주차 노드 기동 신호)

### ③ `health_monitor_node` (C++)
* **역할:** 시뮬레이션 환경 내 차량의 센서 데이터(LiDAR, 카메라)가 정상적으로 발행(Publish)되고 있는지 모니터링합니다.
* **주요 통신:**
  * **Subscribe:** 
    * `/scan` (`sensor_msgs/msg/LaserScan` -> LiDAR 데이터 수신 주기 감시)
    * `/camera/image_raw` (`sensor_msgs/msg/Image` -> 카메라 데이터 수신 주기 감시)
  * **Publish:** `/health_check` (`std_msgs/msg/Bool`)
    * 센서 신호들이 주기적으로 유입되는지 확인하여 최종 정상 작동 여부를 `system_manager`에 전달합니다.

### ④ `vision_ai_node` (Python - PyTorch/YOLO 연동)
* **역할:** 가상 카메라 이미지로부터 주차 기둥, 벽면, 혹은 이동 장애물을 식별합니다. (PyTorch 및 YOLO와 같은 AI 추론 기능의 효율적 연동을 위해 Python 노드로 작성합니다.)
* **주요 통신:**
  * **Subscribe:** `/camera/image_raw` (`sensor_msgs/msg/Image` -> Gazebo 카메라 영상 수신)
  * **Publish:** `/detected_objects` (사용자 정의 메시지 - 인식된 벽면/기둥 및 장애물의 크기와 거리 정보)

### ⑤ `obstacle_avoidance_helper_node` (C++)
* **역할:** Nav2가 경로를 추종하는 동안 3D-LiDAR의 포인트 클라우드 정보와 Vision AI의 객체 인식 정보를 융합하여, 장애물로 인해 전방이 완전히 차단되어 회피 경로를 짤 수 없는 상황(고립 상태)인지 판별합니다.
* **주요 통신:**
  * **Subscribe:** 
    * `/scan` (`sensor_msgs/msg/LaserScan` -> 3D-LiDAR 데이터)
    * `/detected_objects` (Vision AI가 탐지한 객체 데이터)
    * `/plan` (`nav_msgs/msg/Path` -> Nav2 글로벌 경로)
  * **Publish:** `/path_blocked` (`std_msgs/msg/Bool`)
    * 회피할 수 있는 공간이 없다고 판단될 경우 `True`를 발행하여 차량 정지 및 비상 상태 전환을 명령합니다.

### ⑥ `rl_parking_node` (Python - RL Agent)
* **역할:** 차량이 호출기 반경 1m 내로 진입하면 `system_manager`의 신호를 받아 구동되며, 3D-LiDAR와 Vision AI 데이터를 활용해 벽/기둥 밀착 주차를 위한 정밀 속도 제어(`cmd_vel`)를 수행합니다.
* **주요 통신:**
  * **Subscribe:** 
    * `/start_parking` (`std_msgs/msg/Bool` -> 주차 기능 구동 트리거)
    * `/scan` (`sensor_msgs/msg/LaserScan` -> 3D-LiDAR 데이터)
    * `/detected_objects` (기둥 및 벽면 검출 정보)
    * `/odom` (`nav_msgs/msg/Odometry` -> 차량 정밀 위치 및 속도 데이터)
  * **Publish:** 
    * `/cmd_vel` (`geometry_msgs/msg/Twist` -> 주차 시 미세 조종 속도 명령)
    * `/parking_status` (`std_msgs/msg/String` -> 주차 중, 주차 완료 보고)

### ⑦ `Nav2 Stack Nodes` (ROS2 기본 패키지)
* **역할:** 지도를 기반으로 원격 리모컨 위치까지의 글로벌/로컬 경로 계획 및 이동 제어를 담당합니다.
* **주요 통신:**
  * **Subscribe:** `/goal_pose` (`geometry_msgs/msg/PoseStamped` -> 목적지 수신)
  * **Publish:** `/cmd_vel` (`geometry_msgs/msg/Twist` -> Gazebo 로봇에 전달할 일반 주행 명령)

### ⑧ `Gazebo Virtual Robot Simulation Node` (Gazebo 3D Simulator)
* **역할:** 3D 가상 시뮬레이션 환경 내 모형 차량 물리 모델(URDF)을 스폰하여 3D-LiDAR 및 Vision 카메라 센서 데이터를 발행하고, 전달받은 제어 명령(`cmd_vel`)에 따라 구동합니다.
* **주요 통신:**
  * **Publish:**
    * `/scan` (`sensor_msgs/msg/LaserScan` 또는 `PointCloud2` -> 3D-LiDAR 데이터)
    * `/camera/image_raw` (`sensor_msgs/msg/Image` -> 카메라 영상 데이터)
    * `/odom` (`nav_msgs/msg/Odometry` -> 오도메트리 데이터)
    * `/tf` (`tf2_msgs/msg/TFMessage` -> 좌표계 변환 데이터)
  * **Subscribe:**
    * `/cmd_vel` (`geometry_msgs/msg/Twist` -> Nav2 및 RL 주차 노드의 차량 제어 명령)
