# 2026년 08월 20일 대화 기록 (Conversation History)

**작성일시:** 2026-08-20  
**대화 주제:** 2D SLAM 매핑 런치 파일(`slam_mapping.launch.py`) 구조 분석 및 매핑 설정 파일(`mapper_params_online_async.yaml`) 내 세부 파라미터(특히 `loop_search_maximum_distance` 등) 역할과 튜닝 가이드

---

## 🧑 사용자 (User) - Q1

2d지도 생성 시 
slam_mapping.launch.py
실행시켜서 지도를 생성하는데 이 파일을 보니 
launch_sim.launch.py
async_slam_toolbox_node
pointcloud_to_laserscan_node

이렇게 3개를 실행시켜서 지도를 작성하는 것 같아...
지도 작성을 위해 파라미터들은 mapper_params_online_async.yaml에서 불러오는 것 같은데 맞니?

---

## 🤖 어시스턴트 (Antigravity)

**네, 정확하게 파악하셨습니다!**

`slam_mapping.launch.py`는 말씀하신 3가지 구성 요소를 실행하며, 지도 작성 및 변환에 필요한 파라미터 역시 `mapper_params_online_async.yaml`에서 불러와 적용하고 있습니다.

---

### 1. 실행되는 3가지 요소의 역할

1. **`launch_sim.launch.py`**
   - Gazebo 가상 시뮬레이터(주차장 월드) 실행
   - Hunter 로봇 모델(URDF/Xacro) 및 TF 트리 퍼블리시 (`robot_state_publisher`)
   - 조향/주행 제어기(`ackermann_steering_controller`, `joint_state_broadcaster`) 로드 및 로봇 스폰

2. **`pointcloud_to_laserscan_node`**
   - 시뮬레이션의 3D Velodyne LiDAR 데이터(`/points_raw`)를 받아서 2D SLAM 알고리즘이 처리할 수 있는 2D 레이저 스캔(`/scan`) 형태로 슬라이싱/변환

3. **`async_slam_toolbox_node`**
   - 변환된 `/scan` 데이터와 로봇의 오도메트리(`odom` 프레임) 정보를 이용해 실시간으로 지도를 그리고(Mapping), 로봇 위치를 추정(Localization)

---

### 2. 파라미터 파일 로드 방식

`slam_mapping.launch.py`를 확인해보면 다음과 같이 작성되어 있습니다:

```python
# 1. YAML 파일 경로 지정
slam_config_file = os.path.join(pkg_hunter_gazebo, 'config', 'mapper_params_online_async.yaml')

# 2. pointcloud_to_laserscan 노드에 파라미터 전달
start_pointcloud_to_laserscan_node = Node(
    package='pointcloud_to_laserscan',
    executable='pointcloud_to_laserscan_node',
    name='pointcloud_to_laserscan',
    output='screen',
    parameters=[slam_config_file],
    remappings=[
        ('cloud_in', '/points_raw'),
        ('scan', '/scan')
    ]
)

# 3. slam_toolbox 노드에 파라미터 전달
start_async_slam_toolbox_node = Node(
    package='slam_toolbox',
    executable='async_slam_toolbox_node',
    name='slam_toolbox',
    output='screen',
    parameters=[
        slam_config_file
    ]
)
```

`mapper_params_online_async.yaml` 내부에는 두 노드의 네임스페이스(`pointcloud_to_laserscan:`, `slam_toolbox:`)가 명확히 분리되어 있어, 하나의 YAML 파일로 두 노드의 파라미터를 모두 공급하는 구조입니다.

---

## 🧑 사용자 (User) - Q2

mapper_params_online_async.yaml

이 파일에 대해 상세히 알려줘~ 각각 파라미터들이 무슨 역할을 하는지...

---

## 🤖 어시스턴트 (Antigravity)

`mapper_params_online_async.yaml` 파일은 **(1) 3D LiDAR 데이터를 2D LaserScan으로 변환하는 파라미터**와 **(2) SLAM 알고리즘(SLAM Toolbox)의 2D 지도 작성 파라미터**로 나뉘어 있습니다.

각 파라미터의 상세 역할과 의미는 다음과 같습니다.

---

### 1. `pointcloud_to_laserscan` 파라미터
> 3D 포인트클라우드(`/points_raw`)를 받아서 지정한 높이/각도 범위의 데이터만 슬라이스(Slice)하여 2D 평면 스캔(`/scan`)으로 만들어주는 노드의 설정입니다.

| 파라미터명 | 설정값 | 상세 설명 |
| :--- | :--- | :--- |
| **`target_frame`** | `"velodyne_link"` | 변환 기준이 되는 센서 좌표계(TF 프레임)입니다. 라이다 기준 좌표계로 변환합니다. |
| **`transform_tolerance`** | `0.01` (초) | TF(좌표 변환) 데이터의 시간 오차 허용 범위입니다. |
| **`min_height`** | `-0.1` (m) | **슬라이싱 시작 최소 높이(Z)**입니다. 센서(`velodyne_link`, 높이 약 0.35m) 기준 `-0.1m` 아래까지만 스캔에 포함하여 **바닥(Z=0)이 벽(장애물)으로 오인식되는 것을 방지**합니다. |
| **`max_height`** | `1.0` (m) | **슬라이싱 끝 최대 높이(Z)**입니다. 천장이나 공중의 노이즈를 배제하고 센서 위쪽 1.0m 이하 데이터만 추출합니다. |
| **`angle_min`** | `-3.14159` (rad) | 2D 스캔을 생성할 시작 수평 각도 (약 -180도). |
| **`angle_max`** | `3.14159` (rad) | 2D 스캔을 생성할 끝 수평 각도 (약 +180도, 즉 360도 전방위 스캔). |
| **`angle_increment`** | `0.0087` (rad) | 빔(Beam) 사이의 각도 해상도입니다. 약 0.5도(0.0087 rad) 간격으로 2D 레이저 빔을 촘촘히 나눕니다. |
| **`scan_time`** | `0.1` (초) | 스캔 주기 (10Hz 주기, 0.1초마다 1회 스캔). |
| **`range_min`** | `0.3` (m) | 센서와 너무 가까워 로봇 차체(Body)가 찍히는 것을 방지하기 위한 최소 측정 거리(블라인드 존 30cm 설정). |
| **`range_max`** | `20.0` (m) | 2D 레이저 스캔으로 변환할 최대 유효 거리 (20m 밖의 포인트는 무시). |
| **`use_sim_time`** | `true` | Gazebo 시뮬레이션 시간(`/clock`)과 동기화. |

---

### 2. `slam_toolbox` 파라미터
> 2D LaserScan 데이터를 바탕으로 그래프 기반 SLAM(Graph SLAM)을 수행하여 지도를 작성하는 핵심 파라미터입니다.

#### ① 최적화 솔버 설정 (Solver Settings)
SLAM의 핵심인 포즈 그래프(Pose Graph)를 최적화할 때 사용할 비선형 최소제곱법 솔버 라이브러리(Google Ceres Solver) 설정입니다.

- **`solver_plugin`**: `solver_plugins::CeresSolver`
  - Ceres Solver 엔진을 사용하도록 지정합니다.
- **`ceres_linear_solver`**: `SPARSE_NORMAL_CHOLESKY`
  - 희소 행렬(Sparse Matrix) 연산에 최적화된 Cholesky 분해 방식으로, 2D SLAM에서 속도와 정확도의 밸런스가 가장 좋습니다.
- **`ceres_preconditioner`**: `SCHUR_JACOBI`
  - 반복 계산 속도를 높이기 위한 전처리(Preconditioner) 알고리즘입니다.
- **`ceres_trust_strategy`**: `LEVENBERG_MARQUARDT`
  - 널리 쓰이는 비선형 최적화 기법(LM 알고리즘)입니다.
- **`ceres_dogleg_type`**: `TRADITIONAL_DOGLEG`
  - 스텝 크기를 결정하는 Dogleg 최적화 방식입니다.
- **`ceres_loss_function`**: `None`
  - 이상치(Outlier) 페널티 함수를 기본값(손실함수 없음)으로 둡니다.

#### ② ROS 프레임 및 토픽 설정 (ROS Frame & Topic)
- **`odom_frame`**: `odom` (오도메트리 좌표계 이름)
- **`map_frame`**: `map` (글로벌 지도 좌표계 이름)
- **`base_frame`**: `base_link` (로봇 기준 좌표계 이름)
- **`scan_topic`**: `/scan` (입력받을 2D 라이다 스캔 토픽)
- **`use_map_saver`**: `true` (SLAM 완료 후 맵 저장 서비스/노드 활성화)
- **`mode`**: `mapping` (기존 지도를 로드해 위치추정만 하는 `localization` 모드가 아닌, 새 지도를 그리는 `mapping` 모드)

#### ③ 변환 및 시스템 자원 (Transform & Timing)
- **`transform_timeout`**: `0.2` (초)
  - TF 좌표 변환 데이터를 기다리는 타임아웃 시간.
- **`tf_buffer_duration`**: `30.` (초)
  - 과거 30초 동안의 TF 이력을 메모리 버퍼에 보관.
- **`stack_size_to_use`**: `40000000` (약 40MB)
  - SLAM 프로세스가 대규모 그래프를 최적화할 때 스택 오버플로우가 나지 않도록 할당된 스택 메모리 크기.
- **`enable_interactive_mode`**: `true`
  - RViz2 플러그인을 통해 수동으로 노드를 조작하거나 루프를 연결할 수 있게 활성화.

#### ④ 스캔 매칭 및 루프 폐쇄 (Scan Matching & Loop Closing)
- **`use_scan_matching`**: `true`
  - 오도메트리 오차를 보정하기 위해 레이저 스캔 모양을 직접 맞춰보는(Scan Matching) 기능 활성화.
- **`use_scan_barycenter`**: `true`
  - 스캔 매칭 시 기하학적 무게중심을 활용하여 정밀도 향상.
- **`minimum_travel_distance`**: `0.1` (m)
  - 로봇이 **0.1m(10cm) 이상 이동했을 때만** 새로운 노드(스캔 데이터)를 그래프에 추가 (정지 상태에서 불필요한 연산 방지).
- **`minimum_travel_heading`**: `0.1` (rad, 약 5.7도)
  - 로봇이 **약 5.7도 이상 회전했을 때만** 새로운 노드를 그래프에 추가.
- **`scan_buffer_size`**: `10`
  - 스캔 매칭에 참고할 최근 스캔 버퍼 개수.
- **`scan_buffer_maximum_scan_distance`**: `10.0` (m)
  - 버퍼에 담길 스캔의 최대 거리.
- **`link_match_minimum_response_fine`**: `0.1`
  - 노드 간 연결(Link)을 맺을 때 스캔 매칭 점수의 최소 기준 임계값.
- **`link_scan_maximum_distance`**: `1.5` (m)
  - 인접한 스캔 노드를 연결할 최대 거리.
- **`loop_search_maximum_distance`**: `3.0` (m)
  - **루프 클로징(Loop Closing) 탐색 반경**: 이전에 방문했던 장소와 현재 위치의 오차가 3m 이내일 때 같은 장소인지 비교하여 누적 오차를 한 번에 보정.
- **`do_loop_closing`**: `true`
  - 한 바퀴 돌아 제자리로 왔을 때 왜곡된 지도를 반듯하게 펴주는 **루프 클로징 알고리즘 활성화**.

#### ⑤ 지도 해상도 (Map Resolution)
- **`resolution`**: `0.05` (m)
  - 지도 그리드 1칸의 크기 (5cm x 5cm 격자 해상도).
- **`max_laser_range`**: `20.0` (m)
  - SLAM 맵 생성에 반영할 라이다의 최대 유효 거리.

---

## 🧑 사용자 (User) - Q3

loop_search_maximum_distance에 대해 조금 더 자세히 알려줘

---

## 🤖 어시스턴트 (Antigravity)

**`loop_search_maximum_distance`**는 SLAM Toolbox에서 **누적 오차를 한 번에 교정하는 핵심 기능인 '루프 폐쇄(Loop Closure)' 후보를 과거 데이터에서 얼마만큼의 반경 내에서 찾을 것인가**를 결정하는 파라미터입니다.

---

### 1. 배경: 루프 폐쇄(Loop Closure)란?

로봇이 주행할 때 바퀴의 슬립(미끄러짐), 조향 오차 등으로 인해 **오도메트리(Odometry) 오차는 시간이 지날수록 점점 누적**됩니다.

```text
[출발점 A] ─────────→ (크게 한 바퀴 회전) ─────────→ [다시 돌아온 A']
                                                    ↑
                                      오차 누적으로 A와 A'의 위치가 
                                      지도상에서 2m 가량 어긋나 있음!
```

- 로봇이 출발했던 장소로 다시 돌아왔을 때, 누적 오차 때문에 지도가 겹치거나 벽이 두 줄로 생기는 현상(Ghosting)이 발생합니다.
- 이때 SLAM 알고리즘이 **"어? 지금 스캔한 벽 모양이 예전에 A 지점에서 스캔했던 벽 모양과 완전히 똑같은데? 내가 지금 A에 돌아온 거구나!"**라고 알아채고, **과거의 전체 주행 경로와 지도를 반듯하게 쫙 펴서 오차를 0으로 맞추는 과정**을 **루프 폐쇄(Loop Closure)**라고 합니다.

---

### 2. `loop_search_maximum_distance`의 정확한 역할

SLAM을 수행하면서 로봇이 지나간 모든 위치는 **그래프 노드(Node)**로 지도에 계속 기록됩니다.

현재 로봇 위치에서 루프 폐쇄를 시도할 때, **지도의 모든 과거 노드를 일일이 대조하면 연산량(CPU 부하)이 너무 커집니다.**
따라서 SLAM Toolbox는 다음과 같이 거리를 제한합니다:

> **"현재 로봇의 추정 위치를 기준으로 반경 `loop_search_maximum_distance` (예: 3.0m) 이내에 있는 과거 방문 노드들만 골라서 스캔 매칭을 대조해라."**

즉, **루프 후보를 탐색할 가상의 원형 탐색 반경(Search Radius)**을 의미합니다.

---

### 3. 이 값을 바꿨을 때 생기는 현상 (Trade-off)

| 설정값 | 장점 | 단점 / 위험성 |
| :--- | :--- | :--- |
| **너무 작을 때**<br>(예: 0.5m ~ 1.0m) | • 연산량이 적어 CPU 부담이 거의 없음<br>• 엉뚱한 장소를 같은 곳으로 착각할 확률이 낮음 | • **누적 오차가 탐색 반경보다 크면 루프를 감지하지 못함**<br>• 한 바퀴를 크게 돌고 왔는데 루프가 안 닫혀서 **벽이 두 겹으로 그려지거나 지도가 찌그러짐** |
| **너무 클 때**<br>(예: 10.0m ~ 20.0m) | • 오도메트리 오차가 심하게 벌어져도 루프를 잡아낼 가능성이 높아짐 | • **CPU 연산량 급증** (주행 중 순간적인 렉 발생 가능)<br>• **False Positive(잘못된 루프 인식)** 위험:<br>주차장 기둥처럼 **모양이 똑같이 생긴 구조물**이 많은 곳에서 다른 기둥을 같은 기둥으로 착각해 **지도가 완전히 꼬여버릴 수 있음** |

---

### 4. 현재 설정값(`3.0m`)의 의미 및 튜닝 팁

현재 파일에 설정된 **`3.0` (3m)**은 일반적인 실내 및 주차장 환경에서 매우 표준적이고 안정적인 값입니다.

- **이 값을 늘려야 하는 경우 (`4.0` ~ `5.0m`)**:
  - 주차장이 매우 넓어서 로봇이 긴 경로를 주행한 후 출발점으로 복귀했을 때, **오차가 3m 이상 크게 벌어져서 루프가 자동으로 안 닫힐 때**
- **이 값을 유지하거나 줄여야 하는 경우 (`2.0` ~ `3.0m`)**:
  - 주차장 기둥 간격이 좁고 구조가 반복적인데, **엉뚱한 기둥과 매칭되어 지도가 순간적으로 찌그러지는 현상이 발생할 때**
