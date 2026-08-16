# 2026년 08월 16일 대화 기록 (Conversation History)

**작성일시:** 2026-08-16
**대화 주제:** `navigation.launch.py` 구조 분석, Nav2 핵심 7개 노드 역할 및 토픽 흐름, `navigation2` vs `nav2-bringup` 패키지 분석

---

## 🧑 사용자 (User) - Q1

오늘은 bringup_sim_nav2.launch.py에서 실행되는 launch 파일 중 navigation.launch.py에 대해 알아볼 거야.  
그 전에 현재까지의 폴더 구성 및 파일 내용 모두 꼼꼼히 파악해줘~

---

## 🤖 어시스턴트 (Antigravity)

현재 프로젝트 워크스페이스의 전체 폴더 구성과 파일 내용을 꼼꼼하게 분석하여 정리해 드립니다.

---

### 📁 1. 프로젝트 전체 디렉터리 구조

```text
Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/
├── documents/                                  # 프로젝트 기획, 로드맵, 문서 및 분석 자료
│   ├── PRD_Product_Requirements_Document.md    # 제품 요구사항 정의서 (PRD)
│   ├── ROS2_Node_Architecture.md               # ROS2 노드 간 토픽/TF 아키텍처 문서
│   ├── development_process/                    # 개발 단계별 상세 가이드 (Step 01 ~ Step 05)
│   ├── conversation_history_with_ai/           # 이전 대화 히스토리 백업
│   └── study/                                  # 시스템 분석 및 다이어그램 자료
├── issues/                                     # 개발 중 트러블슈팅 및 해결 기록
│   ├── 01_SLAM_Map_Drift_Issue/
│   ├── 02_Nav2_Map_Not_Received_Error_Issue/
│   ├── 03_Nav2_Ackermann_Spin_Issue/
│   └── 04_nav2_ackermann_tuning_troubleshootingN/
└── ros2_ws/                                    # ROS2 개발 워크스페이스
    └── src/
        ├── hunter_robot/                       # AgileX Hunter 아커만 로봇 패키지 모음
        │   ├── hunter_gazebo/                  # 시뮬레이션, 맵, Launch, 파라미터 설정
        │   ├── hunter_description/             # 로봇 URDF/xacro 모델링, 3D LiDAR/센서 설정
        │   ├── hunter_controller/              # 아커만 조향 컨트롤러 플러그인
        │   └── hunter_base/                    # 실 로봇 통신 및 제어 베이스 노드
        └── ugv_sdk/                            # AgileX CAN 통신 SDK 라이브러리
```

---

### 📑 2. 주요 폴더 및 파일별 상세 내용 파악

#### 1) documents/
* **PRD_Product_Requirements_Document.md**: 가상 주차장 환경에서 아커만 조향 모바일 로봇(Hunter)을 원격 호출하여 자율주행하는 프로젝트의 전체 요구사항 및 목표 정의.
* **ROS2_Node_Architecture.md**: 센서-제어-내비게이션 간 노드/토픽/TF 데이터 흐름 정리.
* **development_process/**: 
  * `RM_Step01`: AgileX 시뮬레이션 환경 구축
  * `RM_Step02`: 3D 벨로다인 라이다 센서 통합 및 아커만 조향 제어 검증
  * `RM_Step03`: Gazebo 주차장 월드(`parking_garage.world`) 환경 구축
  * `RM_Step04`: SLAM 기반 2D 그리드 맵 생성
  * `RM_Step05`: Nav2 자율주행 통합 가이드
* **study/launch_node_structure.txt**: 최상위 실행 파일(`bringup_sim_nav2.launch.py`)부터 하위 노드까지의 트리 구조가 정리되어 있음.

---

#### 2) issues/
* **01_SLAM_Map_Drift_Issue**: SLAM 매핑 시 맵 왜곡/드리프트 해결 기록.
* **02_Nav2_Map_Not_Received_Error_Issue**: Nav2에서 Map Server 토픽 QOS 불일치 및 맵 미수신 오류 해결 기록.
* **03_Nav2_Ackermann_Spin_Issue**: 아커만 조향 차량이 제자리 회전(`Spin Recovery`)을 시도하여 발생하는 오류 해결 기록.
* **04_nav2_ackermann_tuning_troubleshootingN**: SmacPlannerHybrid, RegulatedPurePursuitController 등 아커만 특화 튜닝 기록.

---

#### 3) ros2_ws/src/hunter_robot/

##### ① hunter_gazebo (핵심 패키지)
* **launch/**:
  * **bringup_sim_nav2.launch.py**: 시뮬레이션 + 라이다 변환 + Nav2를 한 번에 실행하는 **최상위 통합 런치 파일**
  * **navigation.launch.py**: Nav2의 개별 노드들을 구동하고 라이프사이클을 관리하는 **내비게이션 전용 런치 파일**
  * **launch_sim.launch.py**: Gazebo 주차장 월드 로드, Hunter 모델 스폰, ros2_control(`ackermann_steering_controller`, `joint_state_broadcaster`) 및 `rsp.launch.py` 실행
  * **slam_mapping.launch.py**: `slam_toolbox`를 통한 2D 맵핑 실행 런치
* **config/**:
  * **nav2_params.yaml**: AMCL, SmacPlanner(Hybrid-A*), Regulated Pure Pursuit Controller, Costmap, Behavior Server 등의 상세 설정값
  * **ackermann_controllers.yaml**: ros2_control의 아커만 조향 제어기 설정
* **maps/**: `parking_garage_map.yaml`, `parking_garage_map.pgm` (저장된 2D 그리드 지도)
* **worlds/**: `parking_garage.world` (Gazebo 주차장 시뮬레이션 환경)

##### ② hunter_description
* **rsp.launch.py**: `robot_state_publisher`를 실행하여 URDF(xacro)로부터 TF 변환 트리를 퍼블리시.
* **description/**: Hunter의 기구학 모델, 조향 휠 링크, Gazebo ros2_control 인터페이스, 3D Velodyne LiDAR 센서 정의 xacro 파일들.

---

### 🧭 3. `bringup_sim_nav2.launch.py`와 `navigation.launch.py`의 연결 구조

```text
bringup_sim_nav2.launch.py
├── 1. launch_sim.launch.py (Gazebo & Controller)
├── 2. pointcloud_to_laserscan_node (/points_raw -> /scan)
└── 3. navigation.launch.py (Nav2 Stack)
       ├── map_server (nav2_map_server)
       ├── amcl (nav2_amcl)
       ├── planner_server (nav2_planner: SmacHybrid)
       ├── controller_server (nav2_controller: RegulatedPurePursuit)
       ├── behavior_server (nav2_behaviors)
       ├── bt_navigator (nav2_bt_navigator)
       └── lifecycle_manager_navigation (nav2_lifecycle_manager)
```

`navigation.launch.py`는 `nav2_bringup`의 거대한 기본 launch를 그대로 쓰지 않고, **Hunter 아커만 로봇에 필요한 노드들만 명시적으로 선언하여 관리하도록 직접 커스텀 구현된 형태**입니다.

---

## 🧑 사용자 (User) - Q2

navigation.launch.py 코드 내용 중
```python
    pkg_hunter_gazebo = get_package_share_directory('hunter_gazebo')

    map_yaml_file = LaunchConfiguration('map')
    nav_params_file = LaunchConfiguration('nav_params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
```
이 코드들은 경로를 지정하는거 맞지?

그 이후 DeclareLaunchArgument() 함수를 호출하는데 이건 어떤 역할을 하는 함수지?

---

## 🤖 어시스턴트 (Antigravity)

### 1. `get_package_share_directory`와 `LaunchConfiguration`의 차이

```python
pkg_hunter_gazebo = get_package_share_directory('hunter_gazebo')

map_yaml_file = LaunchConfiguration('map')
nav_params_file = LaunchConfiguration('nav_params_file')
use_sim_time = LaunchConfiguration('use_sim_time')
```

* **`get_package_share_directory('hunter_gazebo')`**:
  * **맞습니다!** 설치된 `hunter_gazebo` 패키지의 **실제 설치 폴더 경로(문자열)**를 가져오는 함수입니다.
* **`LaunchConfiguration(...)`**:
  * 이것은 단순히 '경로'를 지정하는 변수가 아니라, **"런타임(실행 시점)에 결정될 런치 인자(Argument) 값을 담아두는 바구니(참조 객체)"**입니다.
  * `map`과 `nav_params_file`은 파일 경로를 담기 위해 쓰이고, `use_sim_time`은 경로가 아니라 `'true'` / `'false'` 같은 **설정값**을 담습니다.
  * 파이썬의 일반 문자열 변수가 아니라, **외부에서 사용자가 값을 바꿔서 실행할 수 있도록 연결해주는 ROS2 런치 전용 변수**입니다.

---

### 2. `DeclareLaunchArgument()`는 어떤 역할을 하나요?

`DeclareLaunchArgument`는 **"이 런치 파일은 외부(터미널 명령어 또는 상위 런치 파일)에서 인자(Argument)를 전달받을 수 있다"**고 공식적으로 선언하고, **기본값(default_value)**을 정의하는 함수입니다.

```python
declare_map_yaml_cmd = DeclareLaunchArgument(
    'map',
    default_value=os.path.join(pkg_hunter_gazebo, 'maps', 'parking_garage_map.yaml'),
    description='Full path to map yaml file to load')
```

#### 💡 왜 사용할까요?
런치 파일을 실행할 때마다 코드를 직접 수정하지 않고, **터미널 명령어 한 줄로 설정을 바꿀 수 있게 만들기 위함**입니다.

1. **기본값으로 실행할 때** (인자를 따로 주지 않으면 `default_value`로 지정된 주차장 맵이 로드됨):
   ```bash
   ros2 launch hunter_gazebo navigation.launch.py
   ```

2. **다른 맵이나 설정을 외부에서 주입할 때** (코드를 고칠 필요 없이 덮어씌움):
   ```bash
   ros2 launch hunter_gazebo navigation.launch.py map:=/home/tae/my_other_map.yaml use_sim_time:=false
   ```

---

### 🔄 세 함수의 연결 흐름 요약

1. **`get_package_share_directory`**: 패키지 경로를 찾아서 `DeclareLaunchArgument`의 `default_value`를 만들 때 사용합니다.
2. **`DeclareLaunchArgument`**: 외부에서 `map`, `nav_params_file`, `use_sim_time`을 바꿀 수 있는 통로를 열어두고, 안 넘겨주면 쓸 기본값을 등록합니다.
3. **`LaunchConfiguration`**: 최종적으로 결정된 그 값을 꺼내서 아래의 `map_server`, `amcl` 등 각 노드의 `parameters`로 전달합니다.

---

## 🧑 사용자 (User) - Q3

그 이후 7개의 Node()는 노드를 선언하는 코드지?

---

## 🤖 어시스턴트 (Antigravity)

**네, 맞습니다!** 

그 7개의 `Node()` 코드는 **Nav2 자율주행 시스템을 움직이는 7개의 핵심 노드를 선언하고 실행 설정을 정의하는 코드**입니다.

선언된 7개의 노드가 각각 어떤 역할을 맡고 있는지 한눈에 보기 쉽게 정리해 드릴게요.

---

### 🤖 선언된 7개 핵심 노드 역할

| 번호 | 노드 변수명 | 패키지 / 실행 파일 | 담당 역할 (쉽게 이해하기) |
| :--- | :--- | :--- | :--- |
| **1** | `start_map_server_node` | `nav2_map_server` / `map_server` | **지도 제공자**<br>저장된 2D 지도 파일(`.yaml`, `.pgm`)을 읽어서 다른 노드들에게 발행합니다. |
| **2** | `start_amcl_node` | `nav2_amcl` / `amcl` | **위치 추정기 (내비게이션의 GPS)**<br>라이다 센서 데이터와 지도를 대조하여 로봇이 지도상 어디에 있는지 추정합니다. |
| **3** | `start_planner_node` | `nav2_planner` / `planner_server` | **전역 경로 생성기 (Global Planner)**<br>목적지까지 가는 최적의 전체 경로(전역 경로)를 계획합니다. (현재 아커만용 SmacPlanner 사용) |
| **4** | `start_controller_node` | `nav2_controller` / `controller_server` | **로컬 경로 추종 및 속도 명령 생성기 (Local Planner)**<br>계획된 경로를 따라가도록 실시간으로 장애물을 피하며 모터 속도/조향각(`/cmd_vel`)을 계산해 출력합니다. (현재 Pure Pursuit 사용) |
| **5** | `start_behavior_server_node` | `nav2_behaviors` / `behavior_server` | **회복/예외 행동 제어기 (Recovery Behaviors)**<br>로봇이 장애물에 갇히거나 주행이 막혔을 때 후진(`backup`), 대기(`wait`) 등의 탈출 동작을 수행합니다. |
| **6** | `start_bt_navigator_node` | `nav2_bt_navigator` / `bt_navigator` | **전체 행동 총괄 지휘관 (Behavior Tree)**<br>목표 지점 수신부터 경로 계획, 주행, 장애물 회피, 도착까지의 전체 내비게이션 시나리오를 총괄 지휘합니다. |
| **7** | `start_lifecycle_manager` | `nav2_lifecycle_manager` / `lifecycle_manager` | **노드 상태 관리자 (매니저)**<br>위 1~6번 노드들의 생명주기(Unconfigured ➔ Inactive ➔ Active)를 관리하여, 순서대로 정상 활성화(`autostart`)되도록 총괄합니다. |

---

### 💡 동작 방식 요약

1. 코드에서 `Node(...)`로 각 노드의 **패키지명, 실행 파일명, 파라미터 파일(`nav2_params.yaml`), 시뮬레이션 시간 동기화(`use_sim_time`)** 등을 선언합니다.
2. 맨 아래의 `LaunchDescription([...])` 리스트에 이 7개 노드를 담아 반환(`return`)하면, ROS2 런치 시스템이 이 노드들을 백그라운드 프로세스로 띄우게 됩니다.

---

## 🧑 사용자 (User) - Q4

위의 표에서 각 노드가 구독하거나 발행하는 토픽에 관한 컬럼을 추가해서 다시 정리해줄래?

---

## 🤖 어시스턴트 (Antigravity)

각 노드가 주고받는 **주요 구독(Subscribe) 토픽**과 **발행(Publish) 토픽**을 추가하여 알기 쉽게 정리한 표입니다.

---

### 📡 Nav2 7개 핵심 노드의 역할 및 주요 입·출력 토픽

| 번호 | 노드 변수명 (패키지 / 노드) | 주요 역할 | 📥 주요 구독 토픽 (Subscribed) | 📤 주요 발행 토픽 및 TF (Published) |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **`map_server`**<br>(`nav2_map_server`) | **지도 제공** | *(주로 라이프사이클 명령 수신)* | • `/map` (2D 점유 격자 지도)<br>• `/map_metadata` (맵 해상도/크기 정보) |
| **2** | **`amcl`**<br>(`nav2_amcl`) | **로봇 위치 추정**<br>(Localization) | • `/scan` (2D 라이다 센서 데이터)<br>• `/map` (지도 데이터)<br>• `/initialpose` (RViz 초기 위치 설정)<br>• `/tf` (`odom` ➔ `base_link`) | • `/amcl_pose` (추정된 현재 위치)<br>• `/particlecloud` (위치 확률 입자 분포)<br>• **`/tf` (`map` ➔ `odom` 좌표계 변환)** 🌟 |
| **3** | **`planner_server`**<br>(`nav2_planner`) | **전역 경로 생성**<br>(Global Planner) | • `/map` (전역 지도)<br>• `/scan` (정적/동적 장애물 갱신)<br>• `/tf` (좌표 변환)<br>• *`compute_path_to_pose` (목적지 액션 요청)* | • `/plan` (목적지까지의 전체 경로 선)<br>• `/global_costmap/costmap` (전역 위험도 지도)<br>• `/global_costmap/published_footprint` |
| **4** | **`controller_server`**<br>(`nav2_controller`) | **로컬 경로 추종 및 제어**<br>(Local Planner) | • `/plan` (따라갈 경로)<br>• `/odom` (현재 속도/엔코더 주행거리)<br>• `/scan` (실시간 주변 장애물)<br>• `/tf` (좌표 변환) | • **`/cmd_vel` (모터 선속도/각속도 주행 명령)** 🌟<br>• `/local_costmap/costmap` (로컬 위험도 지도)<br>• `/local_costmap/published_footprint` |
| **5** | **`behavior_server`**<br>(`nav2_behaviors`) | **회복 및 예외 행동**<br>(Recovery) | • `/odom` (차량 주행 정보)<br>• `/scan` (충돌 감지용 라이다)<br>• `/tf` (좌표 변환)<br>• *`backup`, `wait` 등의 복구 액션 요청* | • `/cmd_vel` (비상 정지, 후진 탈출 명령) |
| **6** | **`bt_navigator`**<br>(`nav2_bt_navigator`) | **내비게이션 총괄 지휘**<br>(Behavior Tree) | • **`/goal_pose` (사용자가 RViz에서 찍은 최종 목표 위치)**<br>• `/odom`, `/tf` | • `navigate_to_pose` (전체 진행 상태/피드백)<br>• *Planner, Controller, Behavior 노드에 행동 명령 하달(Action Client)* |
| **7** | **`lifecycle_manager`**<br>(`nav2_lifecycle_manager`) | **노드 수명주기 관리** | • 각 노드의 상태 정보 수신 | • 각 관리 대상 노드의 상태 전환 서비스 호출 (`/map_server/change_state` 등)<br>• `transition_event` (노드 상태 변화 알림) |

---

### 💡 핵심 데이터 흐름 요약

1. 사용자가 RViz에서 **`/goal_pose`**를 찍으면 ➔ **`bt_navigator`**가 이를 수신합니다.
2. **`bt_navigator`**의 지휘에 따라 **`planner_server`**가 맵(`/map`)과 라이다(`/scan`)를 바탕으로 최적 경로 **`/plan`**을 만듭니다.
3. **`controller_server`**가 그 경로를 보면서 실시간 장애물을 회피하여 최종 바퀴 구동 명령인 **`/cmd_vel`**을 로봇 제어기로 보냅니다.
4. 이 모든 과정에서 **`amcl`**은 라이다(`/scan`)를 사용해 로봇의 위치를 계산하고 **`map` ➔ `odom` TF**를 맞춰줍니다.

---

## 🧑 사용자 (User) - Q5

7개의 패키지들은 어떤 sudo apt install 로 무엇을 설치해서 이용할 수 있게 된거야?

---

## 🤖 어시스턴트 (Antigravity)

현재 프로젝트(ROS 2 Humble 기준)에서 이 7개 노드와 관련 플러그인들은 **`ros-humble-navigation2` 메타 패키지**를 설치하여 사용할 수 있게 된 것입니다.

---

### 1. 가장 일반적으로 사용하는 한 줄 설치 명령어 (통합 설치)

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup
```

> **`ros-humble-navigation2`**는 "메타 패키지(Meta-package)"여서, 이를 설치하면 Nav2를 구성하는 하위 패키지 수십 개가 의존성으로 자동 함께 설치됩니다.

---

### 2. 개별 패키지 기준 APT 패키지명 매핑

| 번호 | 런치 파일의 `package` 이름 | 실제 설치된 APT 패키지명 |
| :---: | :--- | :--- |
| **1** | `nav2_map_server` | `ros-humble-nav2-map-server` |
| **2** | `nav2_amcl` | `ros-humble-nav2-amcl` |
| **3** | `nav2_planner` | `ros-humble-nav2-planner` |
| **4** | `nav2_controller` | `ros-humble-nav2-controller` |
| **5** | `nav2_behaviors` | `ros-humble-nav2-behaviors` |
| **6** | `nav2_bt_navigator` | `ros-humble-nav2-bt-navigator` |
| **7** | `nav2_lifecycle_manager` | `ros-humble-nav2-lifecycle-manager` |

---

### 💡 [참고] 우리 프로젝트(아커만 제어)에서 함께 사용하는 핵심 추가 패키지

* **아커만 전역 플래너 (Hybrid A*)**: `ros-humble-nav2-smac-planner`
* **아커만 로컬 제어기 (Pure Pursuit)**: `ros-humble-nav2-regulated-pure-pursuit-controller`
* **비용 지도(Costmap) 라이브러리**: `ros-humble-nav2-costmap-2d`
* **3D 라이다 ➔ 2D 변환 노드**: `sudo apt install ros-humble-pointcloud-to-laserscan`

---

## 🧑 사용자 (User) - Q6

ros-humble-navigation2와 ros-humble-nav2-bringup 각각 분리해서 설명해줘

---

## 🤖 어시스턴트 (Antigravity)

`ros-humble-navigation2`와 `ros-humble-nav2-bringup`은 **"엔진(부품)"**과 **"시동/조작 키트(완성형 템플릿)"**의 관계로 이해하시면 아주 명확합니다.

두 패키지를 분리해서 알기 쉽게 설명해 드릴게요.

---

### ⚙️ 1. `ros-humble-navigation2` (핵심 알고리즘 및 엔진 모음)

> **한 줄 요약**: Nav2를 구성하는 **모든 개별 노드, 라이브러리, 알고리즘 플러그인**을 설치해 주는 "핵심 메타 패키지"

* **역할**:
  * 자율주행에 필요한 연산 프로그램(C++ 바이너리 노드)과 플러그인들을 시스템에 설치합니다.
* **포함된 주요 요소**:
  * **핵심 노드**: `nav2_map_server`, `nav2_amcl`, `nav2_planner`, `nav2_controller`, `nav2_behaviors`, `nav2_bt_navigator`, `nav2_lifecycle_manager` 등
  * **경로 계획/제어 알고리즘 플러그인**: 
    * `nav2_smac_planner` (아커만 전용 Hybrid-A* 플래너)
    * `nav2_regulated_pure_pursuit_controller` (아커만 전용 추종 제어기)
    * `nav2_costmap_2d` (장애물 비용 지도 생성 라이브러리)
  * **통신 메시지**: `nav2_msgs` (Nav2 전용 인터페이스)
* **비유**: 자동차를 만들기 위한 **엔진, 조향 장치, 미션, 브레이크 부품 일체**

---

### 🚀 2. `ros-humble-nav2-bringup` (실행용 런치 파일 및 기본 설정 템플릿)

> **한 줄 요약**: 설치된 Nav2 노드들을 한 번에 켜고 테스트할 수 있도록 **표준 Launch 파일, 기본 YAML 설정, RViz 세팅, 데모**를 모아둔 패키지

* **역할**:
  * 사용자가 노드를 하나하나 일일이 런치 파일로 만들지 않아도, 공식적으로 제공하는 표준 런치 파일 하나로 Nav2 전체를 바로 띄울 수 있게 도와줍니다.
* **포함된 주요 요소**:
  * **공식 표준 런치 파일들**:
    * `bringup_launch.py` (전체 통합 런치)
    * `navigation_launch.py` (내비게이션 전용 런치)
    * `localization_launch.py` (AMCL/Map Server 전용 런치)
    * `rviz_launch.py` (Nav2 전용 RViz2 뷰어 실행)
  * **기본 설정 템플릿**:
    * 기본 `nav2_params.yaml` (TurtleBot3 기준 기본 파라미터)
    * 기본 Behavior Tree XML 파일들
  * **시뮬레이션 예제 월드 및 데모 환경**
* **비유**: 공장에서 출고된 **기본 자동차 시동 키, 대시보드 화면, 표준 매뉴얼 세팅값**

---

### 🔍 요약 비교표

| 구분 | `ros-humble-navigation2` | `ros-humble-nav2-bringup` |
| :--- | :--- | :--- |
| **성격** | **핵심 소프트웨어 / 알고리즘 엔진** | **실행 스크립트 / 파라미터 템플릿** |
| **주요 내용물** | 실행 노드 바이너리, C++ 라이브러리, 플러그인 | `.launch.py` 파일, `.yaml` 기본 설정 파일, `.rviz` |
| **사용 목적** | "Nav2 노드들이 내 컴퓨터에서 실행될 수 있게 만든다" | "터미널 명령어 한 줄로 Nav2 전체 시스템을 바로 띄운다" |

---

### 💡 우리 프로젝트에서는 어떻게 쓰고 있나요?

1. **엔진(`navigation2`)**: 우리가 만든 `navigation.launch.py` 안에서 `map_server`, `amcl`, `smac_planner` 등의 **핵심 노드 실행 파일들을 빌려와서 사용**하고 있습니다.
2. **실행 환경(`nav2-bringup`)**: Nav2 공식 bringup은 일반적인 바퀴 2개짜리 로봇(TurtleBot) 기준이라 우리 차량(아커만 조향 로봇 Hunter)에 맞지 않기 때문에, 공식 launch 대신 **우리가 직접 커스텀한 `navigation.launch.py`와 `nav2_params.yaml`을 만들어서 사용**하고 있는 것입니다!
