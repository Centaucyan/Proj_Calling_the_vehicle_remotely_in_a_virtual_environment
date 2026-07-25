# RM Step 01: 개발 환경 구축 및 AgileX(Hunter) 기본 로봇 모델 스폰 가이드

본 문서는 **[프로젝트 개발 로드맵]**의 **1단계: 개발 환경 구축 및 AgileX(Hunter) 기본 로봇 모델 스폰 검증 (`default.world`)**을 성공적으로 수행하기 위한 엔지니어링 상세 실행 가이드입니다.

---

## 1. 개요 및 목표

* **목표:** Ubuntu 22.04 LTS 및 ROS2 Humble 환경에서 AgileX Hunter 로봇의 공식 시뮬레이션 패키지(`hunter_robot`) 및 의존성을 설치하고, Gazebo 경량 기본 월드에서 가상 로봇 모델을 스폰하여 키보드 제어 및 오도메트리 토픽 발행을 검증합니다.
* **주요 검증 요소:**
  - Gazebo 내 AgileX Hunter 로봇 3D 렌더링 및 스폰 정상 여부
  - `teleop_twist_keyboard`를 통한 속도/조향 제어 명령(`cmd_vel`) 전달 여부
  - 오도메트리 토픽(`/odom`) 및 좌표 변환(`/tf`) 데이터 정상 발행 여부

---

## 2. 사전 환경 요구사항

- **OS:** Ubuntu 22.04 LTS (Jammy Jellyfish)
- **ROS 2:** Humble Hawksbill (Desktop-Full)
- **시뮬레이터:** Gazebo Classic (v11)
- **워크스페이스 경로:** `~/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws`

---

## 3. 단계별 상세 실행 절차

### 3.1. [Step 1.1] 시스템 필수 패키지 및 ROS2 컨트롤러 의존성 설치
터미널을 열고 Gazebo 연동 및 로봇 제어에 필요한 핵심 ROS2 패키지를 설치합니다.

```bash
sudo apt update
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-gazebo-ros2-control \
  ros-humble-teleop-twist-keyboard \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-xacro
```

### 3.2. [Step 1.2] AgileX Hunter ROS2 시뮬레이션 및 SDK 서브모듈(Submodule) 추가 (`ros2_ws/src`)
`ros2_ws/src` 디렉터리로 이동하여 ROS2 Humble을 정식 지원하는 Hunter 통합 시뮬레이션 패키지(`hunter_robot`, `humble_dev` 브랜치)와 C++ 빌드 필수 의존성 SDK(`ugv_sdk`)를 Git 서브모듈(Submodule)로 추가합니다.

```bash
cd ~/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src

# 1. ROS2 Humble 지원 Hunter 통합 시뮬레이션 패키지 (humble_dev 브랜치) 서브모듈 추가
git submodule add -b humble_dev https://github.com/LCAS/hunter_robot.git

# 2. hunter_base 빌드 필수 C++ SDK (ugv_sdk) 서브모듈 추가
git submodule add https://github.com/agilexrobotics/ugv_sdk.git

# 3. 서브모듈 최신 상태 동기화 및 내부에 연결된 서브모듈 초기화
git submodule update --init --recursive
```
> **참고:** `hunter_robot` 저장소에는 ROS2 Humble 환경에 호환되는 Gazebo 시뮬레이션(`hunter_gazebo`), 3D URDF 차체 모델(`hunter_description`), 컨트롤러(`hunter_control`), 커스텀 메시지(`hunter_msgs`), 베이스(`hunter_base`)가 통합 수록되어 있습니다.

### 3.3. [Step 1.3] 워크스페이스 빌드 및 환경변수 적용
의존성 패키지를 확인하고 소스코드를 빌드한 후 ROS2 환경 변수를 반영합니다.

```bash
cd ~/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws

# 1. rosdep 데이터베이스 최신화 (최초 1회 환경에서는 사전 `sudo rosdep init` 필요)
rosdep update

# 2. 미설치 의존성 자동 설치 (catkin 경고 키 스킵)
rosdep install --from-paths src --ignore-src -r -y --skip-keys "catkin"

# 3. colcon 빌드 실행
colcon build --symlink-install

# 4. 환경 변수 반영
source install/setup.bash
```

### 3.4. [Step 1.4] Gazebo 시뮬레이션 및 AgileX Hunter 스폰 런치
AgileX Hunter 런치 스크립트를 실행하여 Gazebo 시뮬레이터 상에 로봇을 스폰합니다.

```bash
ros2 launch hunter_gazebo launch_sim.launch.py
```

### 3.5. [Step 1.5] 키보드 텔레옵 수동 조종 및 토픽 검증
새 터미널을 열고 키보드 제어 노드를 실행하여 차량 수동 주행 및 오도메트리 토픽 수신 상태를 검증합니다.

```bash
# 1. 키보드 제어 노드 구동
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 2. 다른 터미널에서 오도메트리 토픽 데이터 모니터링
ros2 topic echo /odom
```

---

## 4. 검증 체크리스트 (Verification Checklist)

| 번호 | 검증 항목 | 검증 방법 및 기준 | 통과 여부 |
|:---:|:---|:---|:---:|
| 1 | **로봇 스폰** | Gazebo 화면 상에 AgileX Hunter 차체와 4개 바퀴가 왜곡 없이 정상 표시됨 | [ ] |
| 2 | **키보드 조종** | `teleop_twist_keyboard` 키 입력 시 차량이 직진 및 곡선 조향 구동함 | [ ] |
| 3 | **/odom 토픽** | 차량 이동 시 `/odom` 데이터의 position/orientation 값이 실시간 업데이트됨 | [ ] |
| 4 | **/tf 좌표계** | `ros2 run tf2_tools view_frames` 실행 시 `odom` -> `base_link` 트리가 올바르게 형성됨 | [ ] |

---

## 5. 트러블슈팅 (Troubleshooting)

* **문제 1: Gazebo 로봇 모델 렌더링 시 메쉬(Mesh) 파일을 찾을 수 없는 경우**
  - **원인:** `GAZEBO_MODEL_PATH` 환경 변수에 AgileX 패키지 경로가 등록되지 않음
  - **해결:** `export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:~/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/hunter_robot` 명령어 실행 후 재시도

* **문제 2: `colcon build` 시 빌드 실패 또는 패키지 누락 오류 발생**
  - **원인:** ROS2 컨트롤러 관련 빌드 필수 라이브러리 누락
  - **해결:** `rosdep install --from-paths src --ignore-src -r -y --skip-keys "ugv_sdk catkin"` 재실행 및 `sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers` 확인
