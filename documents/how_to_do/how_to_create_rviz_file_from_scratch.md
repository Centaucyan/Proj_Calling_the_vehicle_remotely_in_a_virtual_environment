# RViz2 설정 파일(.rviz) 신규 생성 및 환경 구축 가이드

본 문서는 기존에 작성된 RViz 설정 파일(`view_hunter.rviz`)이 없거나 새로 구성해야 할 때, **처음부터 빈 RViz2 환경에서 필요한 시각화 요소를 추가하고 커스텀 `.rviz` 파일로 저장하는 전체 과정**을 정리한 가이드입니다.

---

## 1. 개요 및 사전 준비

### 💡 시뮬레이션/노드를 먼저 실행해야 하는 이유
RViz2 설정 작업을 시작하기 전에 `bringup_sim_nav2.launch.py`(또는 단계에 맞는 런치 파일)를 **먼저 실행**해 두는 것을 강력히 권장합니다.

1. **토픽 자동 탐색 (`[By topic]` 탭 활용):**
   * 노드가 실행 중이면 ROS2 상에 `/points_raw`, `/camera/image_raw`, `/map`, `/plan` 등의 토픽이 활성화됩니다.
   * RViz2에서 토픽 이름을 수동으로 타이핑할 필요 없이 **마우스 클릭만으로 오타 없이 디스플레이를 추가**할 수 있습니다.
2. **실시간 렌더링 확인:**
   * 라이다 포인트클라우드, 전방 카메라 화면, 지도가 화면에 실제로 들어오는 것을 눈으로 보며 색상(Color), 투명도(Alpha), 카메라 뷰(View)를 직관적으로 맞출 수 있습니다.
3. **좌표계(TF) 오류 방지:**
   * 노드가 켜져 있어야 `map -> odom -> base_link` 좌표 변환 트리가 활성화되므로, `Fixed Frame`을 `map`으로 지정했을 때 빨간색 프레임 에러가 발생하지 않습니다.

---

## 2. 단계별 사전 실행 런치 파일 선택

작업하려는 개발 단계에 맞춰 터미널 1에서 시뮬레이션을 먼저 실행합니다.

| 개발 단계 | 실행 런치 파일 | 비고 |
| :--- | :--- | :--- |
| **센서/차체 검증** | `ros2 launch hunter_gazebo launch_sim.launch.py` | 3D-LiDAR, 카메라, 조향 동역학 확인 |
| **SLAM 맵핑** | `ros2 launch hunter_gazebo slam_mapping.launch.py` | 2D 점유 지도 실시간 생성 모니터링 |
| **자율주행 (Nav2)** | `ros2 launch hunter_gazebo bringup_sim_nav2.launch.py` | **추천:** 센서, 맵, 경로 플래닝 풀세트 구성 |

---

## 3. RViz2 파일 생성 및 설정 상세 절차

### 1단계: 시뮬레이션 구동 (터미널 1)
```bash
cd ~/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws
source install/setup.bash
ros2 launch hunter_gazebo bringup_sim_nav2.launch.py
```

---

### 2단계: 빈 상태의 RViz2 실행 (터미널 2)
아무런 설정 파일 옵션(`-d`) 없이 RViz2를 순수 기본 상태로 실행합니다.

```bash
source /opt/ros/humble/setup.bash
rviz2
```

---

### 3단계: 기준 좌표계(Fixed Frame) 설정
1. 좌측 **`Displays`** 패널 최상단의 **`Global Options`** 트리를 확장합니다.
2. **`Fixed Frame`** 항목의 값을 목적에 맞게 변경합니다:
   * **단순 차체/센서 뷰:** `base_link` 또는 `odom`
   * **SLAM 맵핑 및 Nav2 자율주행:** **`map`**

---

### 4단계: 디스플레이 항목 추가 (Displays Add)
좌측 하단의 **`[Add]`** 버튼을 누르고, 상단의 **`[By topic]`** 탭을 클릭하여 다음 항목들을 순서대로 추가합니다.

| 시각화 대상 | 토픽 트리 경로 | 플러그인 타입 (선택 항목) | 설명 |
| :--- | :--- | :--- | :--- |
| **바닥 격자** | `[By display type]` 탭 | **`Grid`** | 지면 기준 눈금 그리드 |
| **로봇 모델** | `/robot_description` | **`RobotModel`** | Hunter 차체 3D 형상 |
| **3D 라이다** | `/points_raw` | **`PointCloud2`** | Velodyne 3D 점구름 데이터 |
| **전방 카메라** | `/camera/image_raw` | **`Camera`** (또는 `Image`) | 실시간 전방 영상 오버레이 |
| **2D 점유 지도** | `/map` | **`Map`** | SLAM/Map Server 정적 지도 |
| **전역 주행 경로** | `/plan` | **`Path`** | Nav2 글로벌 경로 계획선 |
| **지역 주행 경로** | `/local_plan` | **`Path`** | Nav2 로컬 제어 궤적선 (선택) |
| **내비 목적지** | `/goal_pose` | **`Pose`** | 목표 도착점 위치 및 방향 |

> 📌 **노드가 꺼진 상태에서 수동 설정하는 경우 (`[By display type]` 탭 사용):**
> 목록에서 플러그인 종류(`Map`, `PointCloud2` 등)를 생성한 뒤, 우측 세부 설정창의 `Topic` 항목에 위 표의 토픽 이름을 직접 입력합니다.

---

### 5단계: 시각화 옵션 및 뷰 최적화 (권장 튜닝)

1. **`PointCloud2` (3D 라이다):**
   * `Color Transformer` ➡️ **`Intensity`** 또는 **`AxisColor`** 선택
   * `Use rainbow` ➡️ **`true`** 체크 (고저차 및 반사 강도별 색상 구분)
   * `Size (m)` ➡️ `0.02` ~ `0.03`
2. **`Map` (2D 지도):**
   * `Durability Policy` ➡️ **`Transient Local`** 확인
   * `Alpha` ➡️ **`0.7`** (배경 그리드 및 로봇과 겹쳐서 확인 가능하도록 반투명 설정)
3. **`Path` (주행 경로):**
   * `Color` ➡️ 눈에 잘 띄는 색상 지정 (전역 경로: 초록색/빨간색, 지역 경로: 파란색)
   * `Line Width` ➡️ `0.03`
4. **카메라 3D 시점 조정:**
   * 뷰포트 화면에서 마우스 좌클릭(회전), 휠 드래그(이동), 휠 스크롤(줌)을 사용하여 로봇과 지도가 한눈에 들어오는 최적의 앵글을 맞춥니다.

---

### 6단계: 커스텀 `.rviz` 파일로 저장 (`Save Config As`)

1. RViz2 좌측 상단 메뉴에서 **`File` ➡️ `Save Config As`** 를 클릭합니다.
2. 파일 브라우저에서 패키지의 `config` 경로로 이동합니다.
   * 경로: `.../ros2_ws/src/hunter_robot/hunter_gazebo/config/`
3. 파일명을 **`view_hunter.rviz`** (확장자 `.rviz` 포함)로 입력하고 **`[Save]`** 버튼을 클릭합니다.

---

### 7단계: 저장 파일 재사용 및 검증

이후부터는 터미널에서 `-d` 옵션을 주어 저장된 환경을 즉시 불러올 수 있습니다:

```bash
rviz2 -d src/hunter_robot/hunter_gazebo/config/view_hunter.rviz
```

또한 런치 파일(`launch.py`) 내에 `Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config_file])` 형태로 등록하여 시뮬레이션 구동 시 자동 실행되도록 연동할 수 있습니다.
