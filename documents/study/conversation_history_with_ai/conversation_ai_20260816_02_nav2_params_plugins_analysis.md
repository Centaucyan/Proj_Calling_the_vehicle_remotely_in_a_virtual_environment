# 2026년 08월 16일 대화 기록 (Conversation History)

**작성일시:** 2026-08-16
**대화 주제:** `nav2_params.yaml` 노드별 플러그인 분석, 아커만 주행 기구학 (Hybrid-A*, Reeds-Shepp vs Dubins), RPP vs MPPI 제어기 비교 및 파라미터 작성 가이드

---

## 🧑 사용자 (User) - Q1

nav2_params.yaml 내용을 보면
각각 노드마다 plugin이 선언되어 있는데 노드 하나씩 어떤 기능을 하는지 알려줘~ 다른 plugin도 알려주고, 왜 현재 plugin을 사용하는지를 정리해줘~

---

## 🤖 어시스턴트 (Antigravity)

현재 프로젝트의 [nav2_params.yaml](file:///Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml)에 설정된 각 노드별 **플러그인의 역할**, **대안 플러그인**, 그리고 **현재 플러그인을 선택한 이유**를 노드 단위로 알기 쉽게 정리해 드리겠습니다.

---

### 💡 핵심 배경 (현재 로봇 특성)
현재 로봇(Hunter SE)은 **아커만 조향(Ackermann Steering, 자동차 방식)** 로봇입니다.  
일반적인 2륜 차동 구동(Differential Drive) 로봇과 달리 **제자리 회전(Spin-in-place)이 불가능**하고, **물리적인 최소 회전 반경(약 1.6m)** 및 **전륜 조향각 한계**가 존재합니다. 따라서 Nav2 설정도 이에 맞춘 특화 플러그인들로 구성되어 있습니다.

---

## 1. `planner_server` (전역 경로 계획 노드)

출발지에서 목표지점까지 지도 상에서 충돌 없는 전체 경로(Global Path)를 계산하는 노드입니다.

| 항목 | 상세 내용 |
| :--- | :--- |
| **현재 플러그인** | `nav2_smac_planner/SmacPlannerHybrid` (Smac Hybrid-A*) |
| **기능** | 단순 2D 좌표뿐만 아니라 로봇의 **헤딩 각도(Orientation)**, **최소 회전 반경(`minimum_turning_radius: 1.6`)**, **전·후진 모델(Reeds-Shepp 커브)**을 고려하여 실제 자동차가 주행 가능한 매끄러운 궤적을 생성합니다. |

### 🔄 다른 대안 플러그인
* **`nav2_navfn_planner/NavfnPlanner`**: 전통적인 Dijkstra / A* 기반 2D 그리드 플래너. 로봇의 회전 반경이나 차체 방향을 고려하지 않아 차동 구동 로봇에 주로 쓰입니다.
* **`nav2_smac_planner/SmacPlanner2D`**: 2D A* 기반으로 연산 속도가 매우 빠른 플래너 (제자리 회전 가능한 로봇용).
* **`nav2_smac_planner/SmacPlannerLattice`**: State Lattice 그래프를 이용해 제어 공간(Control Space)을 직접 탐색하는 고성능 플래너.
* **`nav2_theta_star_planner/ThetaStarPlanner`**: 그리드 선(45도/90도)에 구애받지 않고 임의 각도(Any-angle) 최단 직선 경로를 생성하는 플래너.

### 🎯 현재 플러그인을 사용하는 이유
* `NavfnPlanner` 같은 기본 플래너를 쓰면 로봇이 회전할 수 없는 직각 코너나 제자리 회전 경로를 계획하여 차가 끼이게 됩니다.
* **`SmacPlannerHybrid`**는 아커만 차량의 **최소 회전 반경(1.6m)** 제약과 **후진 궤적(Reeds-Shepp)** 생성을 완벽히 지원하므로 Hunter 로봇에 가장 적합한 필수 플러그인입니다.

---

## 2. `controller_server` (지역 제어 / 경로 추종 노드)

전역 경로를 받아 장애물을 실시간으로 피하며 실제 모터 속도/조향 명령(`cmd_vel`)을 생성하는 노드입니다.

### ① Controller Plugin
| 항목 | 상세 내용 |
| :--- | :--- |
| **현재 플러그인** | `nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController` (RPP) |
| **기능** | 경로 상의 일정 거리 앞(Lookahead Point)을 바라보며 아커만 기하학에 맞는 조향 곡률과 전진/후진 속도를 부드럽게 계산합니다. 곡률이나 장애물 거리에 따라 속도를 자동 감속하는 기능도 제공합니다. |

* **대안 플러그인**:
  * **`nav2_dwb_controller::DWBLocalPlanner`**: DWA(Dynamic Window Approach) 기반의 ROS2 기본 컨트롤러. 궤적 샘플링 방식이라 차동 구동/옴니휠에 최적화되어 있고 아커만에서는 거동이 불안정합니다.
  * **`nav2_mppi_controller::MPPIController`**: GPU/멀티코어를 활용한 최신 모델 예측 제어(Model Predictive Path Integral). 성능이 매우 뛰어나나 연산량이 큽니다.
  * **`nav2_graceful_controller::GracefulController`**: 최종 목표 지점에 부드러운 곡선으로 정밀하게 정렬 및 주차하는 컨트롤러.
* **현재 플러그인 사용 이유**:
  * 아커만 조향 기구학을 기하학적으로 완벽히 지원하며, 가볍고 안정적입니다.
  * 제자리 회전 시도를 원천 차단(`use_rotate_to_heading: false`)하고 후진 주행(`allow_reversing: true`)을 자연스럽게 수행할 수 있습니다.

### ② Progress Checker Plugin
| 항목 | 상세 내용 |
| :--- | :--- |
| **현재 플러그인** | `nav2_controller::SimpleProgressChecker` |
| **기능** | 설정된 시간(`10.0초`) 동안 최소 이동 거리(`0.5m`) 이상 움직였는지 검사하여 로봇이 장애물에 걸려 멈춰있는지(Stuck) 감지합니다. |
| **대안 / 이유** | 기본 플러그인으로 충분하며, 비정상 정지 상태를 감지해 Recovery 동작을 트리거하기 위해 사용합니다. |

### ③ Goal Checker Plugin
| 항목 | 상세 내용 |
| :--- | :--- |
| **현재 플러그인** | `nav2_controller::SimpleGoalChecker` |
| **기능** | 로봇이 최종 목표 지점의 거리 오차(`0.25m`) 및 각도 오차(`0.25 rad`) 범위 내에 들어왔는지 판별합니다. |
| **대안** | `nav2_controller::StoppedGoalChecker` (오차 범위 내 진입뿐만 아니라 로봇의 속도가 0으로 완전히 멈췄는지까지 추가 검사). |
| **이유** | 목표 도달 여부를 단순하고 명확하게 판별하기에 가장 신뢰성이 높습니다. |

---

## 3. `local_costmap` & `global_costmap` (비용 지도 계층 노드)

장애물, 안전 마진, 정적 지도를 계층화(Layered Costmap)하여 이동 가능 영역의 위험도를 계산합니다.

### ① `StaticLayer` (`nav2_costmap_2d::StaticLayer`)
* **사용 노드**: `global_costmap`
* **기능**: SLAM이나 `map_server`에서 불러온 2D 점유 격자 지도(벽, 고정 구조물)를 기반으로 기본 맵 레이어를 형성합니다.
* **대안**: 없음 (정적 맵 표현의 표준 계층).

### ② `ObstacleLayer` (`nav2_costmap_2d::ObstacleLayer`)
* **사용 노드**: `global_costmap`, `local_costmap`
* **기능**: 2D LiDAR 센서(`/scan`) 데이터를 실시간 수신하여 새롭게 나타난 장애물을 등록(Marking)하고, 사라진 장애물을 지우는(Clearing) 역할을 합니다.
* **대안 플러그인**:
  * **`nav2_costmap_2d::VoxelLayer`**: 3D LiDAR/Depth 카메라용 3D 복셀 레이어.
  * **`spatio_temporal_voxel_layer (STVL)`**: 3D 공간 상에서 시간 경과에 따라 동적 장애물을 감쇠시키는 고성능 레이어.
  * **`nav2_costmap_2d::RangeSensorLayer`**: 초음파/ToF 단거리 센서 전용 레이어.
* **현재 플러그인 사용 이유**:
  * 단일 2D LiDAR 센서를 사용하고 있으므로 `ObstacleLayer`가 가장 가볍고 효율적입니다.

### ③ `InflationLayer` (`nav2_costmap_2d::InflationLayer`)
* **사용 노드**: `global_costmap`, `local_costmap`
* **기능**: 감지된 벽/장애물 주변으로 가상의 위험 비용(Cost Gradient)을 방사형(`inflation_radius: 1.0m`)으로 퍼뜨려 로봇이 벽에 바짝 붙지 않고 안전거리를 유지하며 주행하도록 만듭니다.
* **현재 플러그인 사용 이유**:
  * 로봇의 물리적 차체 크기([footprint](file:///Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml#L120)) 충돌 방지 및 안전 주행 마진 확보에 필수적입니다.

*(참고: 진입 금지 구역 설정 등을 위해 `KeepOutSubLayer`, `SpeedFilterSubLayer` 같은 Costmap Filter 레이어를 추가 확장할 수도 있습니다.)*

---

## 4. `behavior_server` (회복 및 특수 동작 노드)

주행 중 교착 상태(Stuck)나 경로 이탈이 발생했을 때 상황을 탈출하기 위한 회복 동작(Recovery Actions)을 수행합니다.

| 플러그인 | 기능 설명 | 아커만 로봇 적용성 |
| :--- | :--- | :--- |
| **`nav2_behaviors/BackUp`** | 뒤로 일정 거리 후진하여 앞의 장애물 탈출 | 🌟 **매우 유용 (아커만 핵심 복구 동작)** |
| **`nav2_behaviors/Wait`** | 일정 시간 멈춰 서서 동적 장애물이 지나가길 대기 | 🌟 **유용 (통로 대기)** |
| **`nav2_behaviors/DriveOnHeading`**| 조향을 꺾지 않고 지정된 거리만큼 직진 | 🌟 **유용** |
| **`nav2_behaviors/Spin`** | 제자리에서 360도 회전 시도 | ⚠️ **아커만 조향 불가 (사용 지양/제외 권장)** |

* **대안 / 확장**:
  * `nav2_behaviors/AssistedTeleop`: 복구 불가능 시 수동 조종 개입.
  * 아커만 전용 커스텀 복구 동작 (예: T-turn / 3-point-turn 후진 전진 반복 탈출).
* **현재 사용 이유**:
  * 앞이 막혔을 때 뒤로 후진(`backup`)하거나 잠시 멈춰 대기(`wait`)하는 기본 복구 절차를 수행하기 위해 사용합니다.

---

## 5. `bt_navigator` (네비게이션 제어 컨트롤러)

Behavior Tree(행동 트리)를 실행하여 **경로 계획 -> 경로 추종 -> 장애물 감지 -> 복구 동작**의 전체 네비게이션 시퀀스를 총괄 관리하는 오케스트레이터입니다.  
내부 XML 트리에 선언된 네비게이션 액션 노드(BT Action Nodes)들을 적절한 타이밍에 호출합니다.

---

## 📊 노드별 플러그인 한눈에 보기 요약

| 노드 (Node) | 사용 중인 플러그인 (Current Plugin) | 대표 대안 플러그인 | 채택 이유 (Hunter 아커만 로봇 기준) |
| :--- | :--- | :--- | :--- |
| **planner_server** | `SmacPlannerHybrid` | `NavfnPlanner`, `ThetaStarPlanner` | 회전 반경(1.6m) 및 전·후진(Reeds-Shepp)을 반영한 주행 가능 곡선 경로 생성 |
| **controller_server** | `RegulatedPurePursuitController` | `DWBLocalPlanner`, `MPPIController` | 아커만 전륜 조향 곡률 계산에 최적화, 제자리 회전 방지, 안정적인 후진 추종 |
| **costmap (공통)** | `ObstacleLayer` + `InflationLayer` | `VoxelLayer`, `STVL` | 2D LiDAR 데이터 처리 최적화 및 차체 충돌 방지 안전 마진 형성 |
| **costmap (전역)** | `StaticLayer` | - | SLAM 지도의 정적 점유 그리드 반영 |
| **behavior_server** | `BackUp`, `Wait`, `DriveOnHeading` | `AssistedTeleop` | 제자리 회전이 안 되는 차량의 후진/대기 기반 장애물 탈출 |

---

## 🧑 사용자 (User) - Q2

우선 1. planner_server (전역 경로 계획 노드) 여기에서
'단순 2D 좌표뿐만 아니라 로봇의 헤딩 각도(Orientation), 최소 회전 반경(minimum_turning_radius: 1.6), **전·후진 모델(Reeds-Shepp 커브)**을 고려하여 실제 자동차가 주행 가능한 매끄러운 궤적을 생성합니다.' 
이 말의 로봇의 헤딩 각도(Orientation), 최소 회전 반경(minimum_turning_radius: 1.6) 이란게 뭐지?

---

## 🤖 어시스턴트 (Antigravity)

아커만 조향(자동차 방식) 로봇의 주행 특성을 이해하는 데 가장 중요한 두 가지 핵심 개념입니다.  
실제 자동차 운전 상황과 비교하여 직관적으로 설명해 드리겠습니다!

---

### 1. 로봇의 헤딩 각도 (Orientation / Heading, $\theta$ / Yaw)

> **"로봇의 머리(앞 범퍼)가 현재 어느 방향을 쳐다보고 있는가?"**를 뜻하는 각도입니다.

```
       [북쪽] 0°
          ▲ (바라보는 방향 = Heading)
          │
      ┌───┴───┐
      │ 로봇  │   위치: (x, y)
      │ 차체  │   헤딩(방향): θ
      └───────┘
```

#### 💡 왜 자동차 방식에서는 헤딩 각도가 중요할까요?
* **일반 로봇(로봇청소기, 차동 구동):**
  * 위치 $(x, y)$만 알면 됩니다.
  * 동쪽으로 가고 싶으면 **제자리에서 90도 휙 돌아서** 앞으로 가면 그만입니다.
* **자동차 방식 로봇(Hunter):**
  * **제자리 회전이 불가능**합니다.
  * 차가 **'북쪽'**을 보고 서 있다면, 오른쪽(동쪽)으로 가기 위해 **반드시 앞으로 전진하면서 핸들을 꺾어 완만한 곡선을 그리며** 돌아야 합니다.
* **플래너의 차이:**
  * 기본 플래너(`NavfnPlanner` 등): 단순히 점과 점 $(x, y)$만 잇는 꺾인 선을 계획합니다.
  * **현재 플래너(`SmacPlannerHybrid`):** 출발점과 목표점의 위치 $(x, y)$뿐만 아니라 **"어느 각도($\theta$)로 진입해야 하는가"**까지 계산하여 차가 부드럽게 진입할 수 있는 곡선 경로를 만듭니다.

---

### 2. 최소 회전 반경 (`minimum_turning_radius: 1.6`)

> **"핸들을 한쪽 끝까지 다 꺾은 상태에서 한 바퀴 돌았을 때 그려지는 원의 반지름($R$)"**입니다.  
> 단위는 **미터(m)**이며, `1.6`은 **반지름 1.6m (지름 3.2m)**의 원을 의미합니다.

```
                  핸들을 끝까지 꺾고 회전
                     ┌───────────┐
                  ／               ＼
                ／                   ＼
               │          ┌─ R ─┐      │  <-- 반지름(R) = 1.6m
               │          •(중심)      🚗 (Hunter 로봇)
                ＼                   ／
                  ＼               ／
                     └───────────┘
```

#### 💡 왜 이 파라미터가 필수적일까요?
* 실제 Hunter 로봇은 바퀴가 꺾이는 **최대 조향각(Max Steering Angle)**에 물리적 한계가 있습니다.
* 핸들을 끝까지 꺾어도 **반지름 1.6m보다 더 좁고 급격한 원은 물리적으로 돌 수 없습니다.**

#### 🚨 만약 이 값을 설정하지 않거나 일반 플래너를 쓴다면?
1. **일반 플래너:** 아래 그림처럼 모퉁이에서 반지름 0.5m짜리 **급격한 90도 꺾기 경로**를 생성합니다.
2. **로봇의 문제:** 로봇은 핸들을 다 꺾어도 1.6m로 크게 돌기 때문에, **플래너가 준 선을 따라가지 못하고 벽에 충돌**하게 됩니다.

```
[일반 플래너가 짠 경로]        [Smac Hybrid 플래너가 짠 경로]
      │                              │
      │ 급커브 (R=0.5m)              ) 완만한 곡선 (R ≥ 1.6m 보장)
      └───► (충돌 발생!)           ／
                                 └───► (부드럽고 안전하게 주행)
```

---

### 📝 요약

* **헤딩 각도(Orientation):**  
  차량의 앞머리 방향을 고려하여, **"차가 꺾을 수 있는 방향"**으로만 경로를 시작하고 끝내도록 해줍니다.
* **최소 회전 반경(1.6m):**  
  로봇의 핸들 한계를 플래너에게 알려주어, **"실제 이 차가 돌 수 있는 1.6m 이상의 완만한 커브 곡선"**으로만 경로를 짜도록 강제합니다.

---

## 🧑 사용자 (User) - Q3

Dijkstra / A* 이건 경로 계획 알고리즘의 이름이야?

---

## 🤖 어시스턴트 (Antigravity)

**네, 맞습니다!**  
**Dijkstra(다익스트라)**와 **A\*(에이스타)**는 컴퓨터 과학과 로봇 공학, 내비게이션(네이버 지도, T맵 등), 게임 AI에서 가장 널리 쓰이는 **대표적인 최단 경로 탐색 알고리즘**의 이름입니다.

이해하기 쉽게 두 알고리즘의 원리와 차이점을 비유로 정리해 드리겠습니다.

---

### 1. 다익스트라 (Dijkstra) 알고리즘
* **원리 (물 번짐 비유):**  
  출발지점에 잉크 한 방울을 떨어뜨렸을 때 **모든 방향(360도)으로 잉크가 동심원을 그리며 퍼져나가는 방식**입니다.
* **특징:**
  * 목적지가 동쪽에 있든 서쪽에 있든 상관없이, 출발점 주변의 모든 길을 균일하게 탐색합니다.
  * **장점:** 수학적으로 100% 완벽한 최단 경로를 무조건 찾아냅니다.
  * **단점:** 목적지와 반대 방향인 길까지 전부 조사하므로 **계산 시간이 오래 걸리고 비효율적**입니다.

```
       [다익스트라 탐색 방식]
            ↑  ↑  ↑
          ←   출발   →  (목적지가 오른쪽이어도
            ↓  ↓  ↓      모든 방향으로 퍼져나가며 찾음)
```

---

### 2. A* (A-star, 에이스타) 알고리즘
* **원리 (나침반 비유):**  
  다익스트라 알고리즘에 **"목적지가 대략 저 방향에 있으니, 그쪽 길을 먼저 찾아보자!"**라는 **나침반(휴리스틱, Heuristic)**을 더한 방식입니다.
* **핵심 수식:**
  $$\text{총 예상 비용 } f(n) = g(n) + h(n)$$
  * $g(n)$: 출발점에서 현재 위치까지 실제로 온 거리
  * $h(n)$: 현재 위치에서 **목적지까지 남은 직선거리(예상치)**
* **특징:**
  * 목적지 방향에 있는 경로를 우선적으로 탐색하기 때문에, 다익스트라보다 **훨씬 적은 계산으로 빠르게 최단 경로**를 찾아냅니다.
  * 오늘날 대부분의 로봇과 내비게이션의 표준 경로 탐색 알고리즘으로 쓰입니다.

```
       [A* 탐색 방식]
              출발 ──► ──► [목적지]
                   (목적지 방향 위주로 집중 탐색하여 빠름!)
```

---

### 💡 현재 우리 로봇(Hunter)에서 쓰는 `Hybrid-A*`는?

현재 `nav2_params.yaml`에 설정된 **`SmacPlannerHybrid`**는 바로 이 **A\* 알고리즘을 자동차에 맞게 업그레이드한 "하이브리드 A\*(Hybrid-A\*)" 알고리즘**입니다.

1. **기본 A\*:** 
   * 격자 지도(바둑판)에서 상·하·좌·우 픽셀 단위로만 점을 잇기 때문에, 선이 각지고 꺾여서 **자동차가 따라갈 수 없습니다.**
2. **Hybrid-A\*:** 
   * A\*의 빠른 탐색 속도는 그대로 유지하면서,
   * 노드를 연결할 때 바둑판 격자가 아니라 **"자동차가 핸들을 꺾으며 이동하는 곡선(Dubins / Reeds-Shepp 커브)"**을 연결하여 탐색합니다.

> **한 줄 요약:**  
> **Dijkstra** (전 방향 탐색) ➡️ 발전 ➡️ **A\*** (목적지 방향 우선 탐색) ➡️ 자동차용 발전 ➡️ **Hybrid-A\*** (현재 로봇이 쓰는 회전 곡선 반영 A\*)

---

## 🧑 사용자 (User) - Q4

로봇의 헤딩 각도(Orientation), 최소 회전 반경을 고려하는 플러그인은 nav2_smac_planner/SmacPlannerHybrid 이것밖이야?

---

## 🤖 어시스턴트 (Antigravity)

아닙니다! **`SmacPlannerHybrid`가 가장 대표적이고 표준으로 널리 쓰일 뿐, 다른 플러그인과 방식들도 존재합니다.**

Nav2 생태계 및 로봇 공학에서 **로봇의 방향(Orientation)**과 **최소 회전 반경(회전 제약)**을 고려할 수 있는 다른 플러그인들을 정리해 드립니다.

---

### 1. Nav2 공식 지원 플러그인

#### ① `nav2_smac_planner/SmacPlannerLattice` (스테이트 래티스 플래너)
* **방식:** 로봇이 물리적으로 움직일 수 있는 작은 곡선 궤적 조각들(**Motion Primitives**, 예: 10도 우회전, 20도 좌회전, 후진 등)을 미리 수식으로 만들어 두고, 이를 레고 블록처럼 이어 붙여 경로를 찾습니다.
* **특징:** 아커만 차량뿐만 아니라 복잡한 다관절 로봇, 트레일러가 달린 트럭 등 **원하는 모든 물리적 회전 제약 조건을 완벽하게 반영**할 수 있습니다.
* **단점:** 로봇의 물리 특성에 맞는 모션 프리미티브 파일(`.json`)을 사전에 직접 생성해야 해서 설정이 다소 까다롭습니다.

#### ② `nav2_constrained_smoother` (경로 스무더 결합 방식)
* **방식:** 2D A\*나 Theta\* 같은 빠른 일반 플래너로 대략적인 길을 먼저 찾은 뒤, 후처리(Smoothing) 단계에서 **"곡률이 최소 회전 반경(1.6m)보다 좁아지지 않도록 둥글게 펴주는"** 최적화 알고리즘을 적용합니다.
* **단점:** 넓은 도로에서는 부드럽게 잘 작동하지만, 좁은 막다른 골목이나 후진 주차(K-turn)가 필요한 복잡한 상황에서는 실제 주행 가능한 경로를 못 찾을 수 있습니다.

---

### 2. ROS2 커뮤니티 / 서드파티(외부) 플러그인

#### ③ `TEB Local Planner` (`teb_local_planner`)
* **방식:** **Timed-Elastic-Band(시간 탄성 밴드)** 알고리즘 기반입니다.
* **특징:** 
  * 파라미터로 `min_turning_radius: 1.6`과 아커만 기구학을 직접 지정할 수 있습니다.
  * 경로 계획(Planning)과 제어(Control)를 실시간으로 동시에 수행하며, 움직이는 동적 장애물을 회피하는 능력이 매우 뛰어납니다.
* **단점:** 연산량(CPU 사용량)이 매우 크며, 복잡한 맵에서 로봇이 경로를 잡지 못하고 진동(Oscillation)하는 경우가 있습니다.

#### ④ OMPL 기반 샘플링 플래너 (RRT\* / Informed RRT\*)
* **방식:** 무작위로 점을 뿌려가며 선을 잇는 RRT(Rapidly-exploring Random Tree) 계열 알고리즘 중 **Reeds-Shepp 커브 모델**을 적용한 플래너입니다.
* **특징:** 장애물이 복잡하고 미로 같은 환경에서도 고차원 회전 각도 제약을 만족하는 경로를 찾아냅니다.
* **단점:** 무작위 샘플링 방식 특성상 실행할 때마다 경로 모양이 조금씩 달라지며, 좁은 통로 탐색에 시간이 걸릴 수 있습니다.

---

### 💡 그럼에도 왜 다들 `SmacPlannerHybrid`를 쓸까요?

| 비교 항목 | `SmacPlannerHybrid` (현재 사용) | `SmacPlannerLattice` | `TEB Planner` |
| :--- | :---: | :---: | :---: |
| **아커만 최소 회전반경 지원** | **완벽 지원 (Reeds-Shepp)** | 완벽 지원 (Primitive) | 완벽 지원 (최적화) |
| **설정 난이도** | **쉬움 (반경 숫자만 입력)** | 어려움 (궤적 생성 필요) | 보통 (파라미터 매우 많음) |
| **계산 속도** | **매우 빠름 (수 ms 단위)** | 빠름 | 느림 (CPU 부담 큼) |
| **좁은 공간 전후진 주차** | **매우 자연스러움** | 지원 | 가끔 진동 발생 |
| **Nav2 공식 유지보수** | **Nav2 공식 핵심 플러그인** | Nav2 공식 플러그인 | 서드파티 포팅 버전 |

> **결론:**  
> 다른 대안들도 존재하지만, **`SmacPlannerHybrid`**가 설정이 가장 간단하고, 연산 속도가 압도적으로 빠르며, Nav2 공식 팀에서 아커만/자율주행용으로 가장 심혈을 기울여 최적화해 둔 **"사실상의 표준(De-facto Standard)"**이기 때문에 현재 프로젝트에서도 이를 사용하고 있습니다.

---

## 🧑 사용자 (User) - Q5

자동차가 핸들을 꺾으며 이동하는 곡선(Dubins / Reeds-Shepp 커브)에서 Dubins와 Reeds-Shepp 커브라는게 뭐지?

---

## 🤖 어시스턴트 (Antigravity)

**Dubins(듀빈스)**와 **Reeds-Shepp(리즈-셉)** 커브는 자율주행과 로봇 공학에서 **"자동차가 최소 회전 반경을 지키면서 두 지점 사이를 가장 짧게 이동할 수 있는 최단 곡선 경로"**를 수학적으로 계산해 낸 모델입니다.

두 커브의 가장 결정적인 차이는 바로 **"후진(Reverse)이 가능한가?"**입니다.

---

### 1. 기본 구성 요소 (L, R, S)

자동차가 움직일 수 있는 동작은 크게 3가지 기하학적 요소로 이루어집니다:
* **L (Left)**: 핸들을 왼쪽으로 끝까지 꺾고 도는 원호(곡선)
* **R (Right)**: 핸들을 오른쪽으로 끝까지 꺾고 도는 원호(곡선)
* **S (Straight)**: 핸들을 똑바로 펴고 달리는 직선

이 세 가지를 조합하여 최단 경로를 만들어 냅니다.

---

### 2. Dubins (듀빈스) 커브 — ✈️ "오직 전진만 가능"

1957년 수학자 레스터 듀빈스(Lester Dubins)가 제안한 모델입니다.

* **동작 특징:** 후진 기어가 없어서 **오직 앞으로 전진(Forward only)**만 하면서 목표 방향에 도달해야 합니다.
* **적용 대상:** **비행기, 드론, 고속 보트**, 또는 후진을 하지 않는 고속 도로 자율주행.
* **경로 형태 (총 6가지 조합):**
  * 원호-직선-원호 형태: $LSL, LSR, RSL, RSR$ (예: 좌회전 후 직진 후 우회전)
  * 원호-원호-원호 형태: $LRL, RLR$ (직선 없이 연속으로 꺾는 급선회)
* **단점:** 좁은 골목길이나 주차 공간에서 차를 돌리려면 후진을 못 하므로 **아주 크게 한 바퀴 뺑 돌아서(U턴)** 가야 합니다.

```
[Dubins 커브 예시 (LSR)]
     출발 ──(좌회전 L)──► ──(직선 S)──► ──(우회전 R)──► 목표
```

---

### 3. Reeds-Shepp (리즈-셉) 커브 — 🚗 "전진 + 후진 모두 가능"

1990년 수학자 리즈(Reeds)와 셉(Shepp)이 듀빈스 커브를 확장하여 완성한 모델입니다.

* **동작 특징:** 전진뿐만 아니라 **후진(Reverse) 기어**를 넣고 뒤로 가는 것을 허용합니다.
* **적용 대상:** **일반 자동차, 주차 보조 시스템(T자/평행 주차), 실내 물류 로봇(Hunter)**.
* **경로 형태:**
  * 전진(+)과 후진(-)을 조합하여 총 48가지 패턴을 가집니다.
  * 대표적인 예: **3점 턴 (K-턴 / T자 턴)**
    * 앞으로 좌회전($L^+$) ➡️ 후진으로 우회전($R^-$) ➡️ 다시 앞으로 좌회전($L^+$)
* **장점:** 좁은 막다른 골목에서도 차를 앞뒤로 뺐다 넣었다 하면서 **최소한의 공간만으로 방향을 180도 바꿀 수 있습니다.**

```
[Reeds-Shepp 커브 예시 (좁은 공간 회전 - K턴)]
           (1) 앞으로 좌회전 (L+)
          ╭─────────►
          │
  출발 ───┘  ▲
             │ (2) 후진으로 우회전 (R-)
             ▼
          ┌─────────► (3) 다시 앞으로 (L+) ──► 목표
```

---

### 💡 `nav2_params.yaml`의 실제 설정과 연결

현재 프로젝트의 [nav2_params.yaml:L93-L94](file:///Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml#L93-L94) 파일을 보면 다음과 같이 설정되어 있습니다:

```yaml
planner_server:
  ros__parameters:
    GridBased:
      plugin: "nav2_smac_planner/SmacPlannerHybrid"
      # motion_model_for_search: "DUBIN"        # 👈 전진만 허용 (비활성화)
      motion_model_for_search: "REEDS_SHEPP"   # 👈 전진 + 후진 허용 (선택됨!)
      minimum_turning_radius: 1.6
      reverse_penalty: 1.5                     # 👈 후진할 때 주는 벌점 (꼭 필요할 때만 후진하도록 유도)
```

* **`REEDS_SHEPP`를 선택한 이유:**  
  실내나 복잡한 가상 환경에서 차가 막다른 길에 갇히거나 좁은 코너를 만났을 때, 전진만 고집하다가 길을 못 찾는 문제를 방지하고, **실제 자동차처럼 앞뒤로 차를 빼가며 목적지까지 영리하게 찾아가도록 하기 위함**입니다.
* **`reverse_penalty: 1.5`:**  
  후진이 가능하다고 해서 평지에서 아무 때나 뒤로 가면 안 되므로, **"전진 경로가 있으면 가급적 전진하고, 정말 좁아서 안 될 때만 후진을 써라"**는 벌점(가중치) 설정입니다.

---

## 🧑 사용자 (User) - Q6

README.md에 아래와 같은 내용을 넣었다.

경로 계획 사용 알고리즘:
Hybrid-A*: A* 알고리즘은 격자 지도에서 상하좌우 픽셀 단위로만 점을 잇기 때문에 경로가 각지고 꺾이는 것을 곡선을 반영하여 탐색함.
곡선 계산 모델 Reeds-Shepp: 전후진 모두 고려하여 곡선 계산. (참고. Dubins: 전진만 고려하여 곡선 계산)

내가 적은 내용이 맞는거니?

---

## 🤖 어시스턴트 (Antigravity)

**네, 완벽하게 맞습니다! 핵심을 아주 정확하고 명확하게 잘 요약하셨습니다. 👍**

작성하신 문장은 다음의 핵심 포인트들을 군더더기 없이 정확히 담고 있습니다:
1. **A\*의 한계** (격자 단위 점 연결로 인한 각진 경로)
2. **Hybrid-A\*의 차별점** (차량 주행을 위한 곡선 반영 탐색)
3. **Reeds-Shepp vs Dubins의 차이** (전·후진 지원 여부)

---

### 💡 (선택 사항) README에 더 깔끔하게 들어갈 수 있는 마크다운 서식 예시

작성하신 내용을 README에서 다른 사람이 읽기 편하도록 서식을 조금 정돈한 예시입니다. 필요하시면 참고해서 사용해 보세요!

```markdown
- **경로 계획 알고리즘 (Global Planner): `Hybrid-A*`**
  - 기존 A* 알고리즘의 한계(격자 지도 기반으로 인한 각진 경로)를 보완하여, 차량이 주행 가능한 부드러운 **회전 곡선 궤적**을 반영해 탐색.
- **곡선 궤적 모델: `Reeds-Shepp`**
  - 전진뿐만 아니라 **후진 주행까지 고려**하여 좁은 공간이나 막다른 길에서도 K-턴(3-Point Turn)을 통해 경로를 계획. *(참고: Dubins 모델은 전진 주행만 고려)*
```

---

## 🧑 사용자 (User) - Q7

곡선 궤적 모델도 경로 계획에 속에 있는거 아니야?

---

## 🤖 어시스턴트 (Antigravity)

**네, 맞습니다! 아주 정확하게 짚으셨습니다.**

**Reeds-Shepp**은 별개의 독립된 알고리즘이 아니라, **Hybrid-A\* 알고리즘 내부에서 사용하는 '차량 모션 모델(Motion Model)'**입니다.

---

### 💡 구조로 보면 이런 관계입니다:

$$\text{경로 계획 (Global Path Planning)}$$
$$\downarrow$$
$$\text{알고리즘: } \mathbf{Hybrid\text{-}A^*}$$
$$\downarrow \text{ (내부에서 차가 움직이는 곡선을 계산할 때)}$$
$$\text{모션 모델: } \mathbf{Reeds\text{-}Shepp \text{ (전·후진 곡선)}}$$

Hybrid-A*가 길을 찾을 때 **"노드와 노드를 어떤 곡선으로 연결할 것인가?"**를 결정하는 수학 공식 도구가 바로 **Reeds-Shepp 모델**입니다.

---

### 📝 계층 구조를 살린 README 권장 정리 방식

따라서 README에 적으실 때도 따로 분리하지 않고, **Hybrid-A\* 아래의 하위 항목(세부 모델)**으로 넣어주시면 기술적으로 훨씬 정확합니다!

```markdown
- **경로 계획 알고리즘 (Global Planner): `Hybrid-A*`**
  - **개요**: 기존 A* 알고리즘의 한계(격자 지도 기반의 각진 경로)를 보완하여, 차량이 주행 가능한 곡선 궤적을 반영해 탐색.
  - **곡선 모션 모델 (`Reeds-Shepp`)**: 전진과 후진을 모두 고려한 곡선을 생성하여 좁은 공간이나 코너에서도 탈출 경로 계획 가능. *(참고: 전진 전용은 Dubins 모델)*
```

---

## 🧑 사용자 (User) - Q8

controller_server에서 desired_linear_vel, transform_tolerance 등 키 이름을 다르게 하면 안되잖아. 이런 키 이름은 어느 문서를 참고해서 작성할 수 있지?

---

## 🤖 어시스턴트 (Antigravity)

Nav2의 파라미터 키 이름(`desired_linear_vel`, `transform_tolerance` 등)은 C++ 소스 코드 내에 등록된 변수명과 100% 일치해야 작동합니다.

이러한 정확한 키 이름과 설명은 다음 **4가지 방법(공식 문서, 공식 템플릿, 터미널 CLI, 소스코드)**을 통해 확인할 수 있습니다.

---

### 1. Nav2 공식 문서 (가장 추천 ⭐)

Nav2 공식 웹사이트의 **[Configuration Guide (설정 가이드)]** 페이지에 모든 플러그인의 파라미터 이름, 자료형(Type), 기본값(Default), 상세 설명이 표로 완벽하게 정리되어 있습니다.

* **Nav2 공식 문서 홈:** [https://docs.nav2.org/configuration/index.html](https://docs.nav2.org/configuration/index.html)
* **주요 플러그인별 공식 파라미터 문서 링크:**
  * **Regulated Pure Pursuit Controller (현재 쓰시는 제어기):**  
    `https://docs.nav2.org/configuration/packages/configuring-regulated-pp.html`
  * **Smac Planner Hybrid (현재 쓰시는 플래너):**  
    `https://docs.nav2.org/configuration/packages/configuring-smac-planner.html`
  * **Costmap 2D (레이어 설정):**  
    `https://docs.nav2.org/configuration/packages/configuring-costmaps.html`
  * **Controller Server (일반 설정):**  
    `https://docs.nav2.org/configuration/packages/configuring-controller-server.html`

> 💡 **Tip:** 구글에 `nav2 regulated pure pursuit parameters` 또는 `nav2 smac planner parameters`라고 검색하면 해당 문서 페이지로 바로 이동합니다.

---

### 2. ROS2 패키지에 내장된 기본 템플릿 파일 확인

Ubuntu에 ROS2와 Nav2를 설치하셨다면, 시스템 내부에 Nav2 팀이 미리 작성해 둔 표준 파라미터 원본 파일이 들어있습니다.

터미널에서 아래 명령어로 기본 파일을 열어보거나 복사해서 쓸 수 있습니다:

```bash
# 기본 템플릿 파일 위치 확인 및 내용 보기
cat /opt/ros/$ROS_DISTRO/share/nav2_bringup/params/nav2_params.yaml
```

---

### 3. 터미널 명령어로 직접 확인 (ROS2 CLI)

Nav2 노드가 실행 중일 때, 해당 노드가 어떤 파라미터 키를 등록하고 있는지 터미널에서 즉시 조회할 수 있습니다.

```bash
# 1. controller_server가 가진 모든 파라미터 키 이름 목록 확인
ros2 param list /controller_server

# 2. 특정 파라미터의 타입 및 설명 확인
ros2 param describe /controller_server FollowPath.desired_linear_vel

# 3. 현재 실행 중인 노드의 모든 설정을 YAML 형식으로 파일로 덤프(추출)
ros2 param dump /controller_server
```

---

### 4. Nav2 GitHub 소스 코드 직접 확인

Nav2는 오픈소스이므로 GitHub의 C++ 코드에서 `declare_parameter` 함수를 검색해 보면 정확한 키 문자열을 확인할 수 있습니다.

* **GitHub:** [https://github.com/ros-navigation/navigation2](https://github.com/ros-navigation/navigation2)
* 예: `nav2_regulated_pure_pursuit_controller` 소스 코드 내부:
  ```cpp
  declare_parameter("desired_linear_vel", 0.5);
  declare_parameter("lookahead_dist", 0.6);
  ```

---

### 📌 요약
새로운 플러그인을 도입하거나 파라미터를 수정할 때는 **[Nav2 Configuration Documentation](https://docs.nav2.org/configuration/index.html)**을 기준으로 작성하시는 것이 가장 정확하고 안전합니다!

---

## 🧑 사용자 (User) - Q9

만약 controller_server의 FollowPath 플러그인을 nav2_mppi_controller::MPPIController으로 변경하려면 nav2_params.yaml 파일을 어떻게 수정하면 되니?
수정하지말고 대화방에서 보여줘~

---

## 🤖 어시스턴트 (Antigravity)

실제 파일은 수정하지 않고, **Hunter(아커만 조향) 로봇에 맞춘 `MPPIController` 설정 예시**를 대화방에 상세히 보여드리겠습니다.

---

### 1. `nav2_params.yaml`의 `controller_server` 수정 예시

`FollowPath` 섹션의 `plugin`과 하위 파라미터들을 다음과 같이 교체하시면 됩니다.

```yaml
controller_server:
  ros__parameters:
    use_sim_time: True
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.5
    min_theta_velocity_threshold: 0.001
    failure_tolerance: 0.3
    progress_checker_plugin: "progress_checker"
    goal_checker_plugins: ["general_goal_checker"]
    controller_plugins: ["FollowPath"]

    progress_checker:
      plugin: "nav2_controller::SimpleProgressChecker"
      required_movement_radius: 0.5
      movement_time_allowance: 10.0

    general_goal_checker:
      stateful: True
      plugin: "nav2_controller::SimpleGoalChecker"
      xy_goal_tolerance: 0.25
      yaw_goal_tolerance: 0.25

    # 🌟 MPPI (Model Predictive Path Integral) Controller 설정 (아커만 모드)
    FollowPath:
      plugin: "nav2_mppi_controller::MPPIController"
      time_steps: 56                 # 미래 예측 시간 스텝 (56 * 0.05s = 약 2.8초 앞 예측)
      model_dt: 0.05                 # 시뮬레이션 시간 간격 (dt)
      batch_size: 1000               # 샘플링할 가상 주행 궤적 개수 (CPU 부하에 따라 800~2000 조절)
      iteration_count: 1             # 최적화 반복 횟수
      vx_std: 0.2                    # 속도 샘플링 표준편차
      vy_std: 0.0                    # Y축(옆으로 이동) 편차 (아커만은 0으로 고정)
      wz_std: 0.4                    # 각속도(조향) 샘플링 표준편차
      vx_max: 1.4                    # 최대 전진 속도 (m/s)
      vx_min: -0.5                   # 최대 후진 속도 (m/s) - 후진 허용
      vy_max: 0.0                    # Y축 속도 (아커만은 0)
      wz_max: 1.0                    # 최대 각속도 (rad/s)
      prune_distance: 1.5            # 지난 경로 정리 거리
      transform_tolerance: 0.2
      motion_model: "Ackermann"      # 🌟 아커만 조향 모션 모델 지정! (DiffDrive / Ackermann / Omni 지원)
      visualize: false               # RViz로 수천 개의 샘플 궤적 시각화 여부 (디버깅용, CPU 절약 위해 false 권장)

      # 🌟 Critics: 수천 개의 궤적 중 '최선의 궤적'을 고르는 채점 기준들
      critics: [
        "ConstraintCritic", 
        "ObstaclesCritic", 
        "GoalCritic", 
        "GoalAngleCritic", 
        "PathAlignCritic", 
        "PathFollowCritic", 
        "PathAngleCritic", 
        "PreferForwardCritic"
      ]

      ConstraintCritic:              # 최대 가속도/속도 제한 준수 여부 채점
        enabled: true
        cost_power: 1
        cost_weight: 4.0

      ObstaclesCritic:               # 장애물 충돌 위험 채점 (충돌 시 매우 큰 벌점)
        enabled: true
        cost_power: 1
        repulsion_weight: 1.5
        critical_weight: 20.0
        consider_footprint: true      # 로봇 차체 외곽선(Footprint) 충돌 검사
        collision_cost: 10000.0
        collision_margin_distance: 0.1
        near_goal_distance: 0.5

      GoalCritic:                    # 최종 목적지에 얼마나 가까워지는가
        enabled: true
        cost_power: 1
        cost_weight: 5.0
        threshold_to_consider: 1.4

      GoalAngleCritic:               # 목표 지점 도착 시 목표 방향과 얼마나 일치하는가
        enabled: true
        cost_power: 1
        cost_weight: 3.0
        threshold_to_consider: 0.5

      PathAlignCritic:               # 전역 경로(Global Path)의 모양을 얼마나 잘 따르는가
        enabled: true
        cost_power: 1
        cost_weight: 10.0
        max_path_occupancy_ratio: 0.05
        trajectory_point_step: 3
        threshold_to_consider: 0.5
        offset_from_furthest: 20
        use_path_orientations: false

      PathFollowCritic:              # 전역 경로를 앞쪽으로 얼마나 진도(Progress)를 나가는가
        enabled: true
        cost_power: 1
        cost_weight: 5.0
        offset_from_furthest: 5
        threshold_to_consider: 1.4

      PathAngleCritic:               # 경로의 곡선 각도와 로봇 헤딩 각도의 일치도
        enabled: true
        cost_power: 1
        cost_weight: 2.0
        offset_from_furthest: 4
        mode: 0
        threshold_to_consider: 0.5

      PreferForwardCritic:           # 웬만하면 후진보다 전진 주행을 선호하도록 유도
        enabled: true
        cost_power: 1
        cost_weight: 5.0
        threshold_to_consider: 0.5
```

---

### 💡 주요 핵심 파라미터 포인트

1. **`motion_model: "Ackermann"`**
   * MPPI 컨트롤러에게 이 로봇이 횡방향(Y축) 이동이 불가능하고 전륜 조향을 하는 아커만 차량임을 알려줍니다.
2. **`batch_size: 1000`**
   * 한 주기(0.05초)마다 **1,000개의 가상 미래 주행 경로를 순간적으로 시뮬레이션**하여 그중 가장 안전하고 빠른 경로를 선택합니다. (CPU가 버벅이면 600~800으로 낮추고, 여유가 있으면 1500~2000으로 올릴 수 있습니다.)
3. **`critics` (채점 기준들)**
   * MPPI는 수천 개의 후보 궤적을 만들고 각 Critic(장애물 회피, 경로 추종, 전진 선호 등)의 점수를 종합해 최적의 핸들 조향각과 가속도를 결정합니다.

---

### ⚠️ 변경 전 체크 사항 (패키지 설치 여부)
MPPI 컨트롤러를 사용하려면 시스템에 패키지가 설치되어 있어야 합니다:
```bash
sudo apt install ros-humble-nav2-mppi-controller
```

---

## 🧑 사용자 (User) - Q10

이게 planner_server에서 경로가 계산되면 controller_server에서 그 경로로 이동하면서 강화학습처럼 보상을 주는 개념으로 실시간 경로가 수정되는건가?

---

## 🤖 어시스턴트 (Antigravity)

**네, 맞습니다! 정말 핵심을 정확하게 꿰뚫어 보셨습니다! 👏**

실제로 **MPPI(Model Predictive Path Integral)** 알고리즘은 **강화학습(RL)과 제어공학(Optimal Control)의 개념이 결합된 최신 알고리즘**입니다. 

말씀하신 대로 **"실시간 시뮬레이션 + 보상/벌점(Cost/Reward)"** 방식으로 작동합니다. 구체적으로 어떻게 동작하는지 쉽게 정리해 드릴게요.

---

### 1. `planner_server`와 `controller_server`의 역할 분담

* **`planner_server` (내비게이션 안내원 - 큰 그림):**
  * 전체 지도를 보고 출발지부터 목적지까지의 **큰 가이드라인(전역 경로, Global Path)**을 제시합니다.
  * *"이 큰 길을 따라서 쭉 가세요"* 하고 선을 그어줍니다.

* **`controller_server` (실제 드라이버 - 순간 판단):**
  * 운전석에 앉아서 앞을 보며 **초당 20번(20Hz)** 핸들과 액셀을 조작합니다.
  * 글로벌 경로를 참고하되, 바로 앞에 갑자기 장애물이 나타나면 피해야 합니다.

---

### 2. MPPI가 "보상/벌점"으로 운전하는 원리 (초당 20회 반복)

MPPI는 매 순간(0.05초마다) 다음과 같은 과정을 거칩니다:

```
                  [현재 로봇 위치]
                         │
        ┌────────────────┼────────────────┐
        ▼ (궤적 1)       ▼ (궤적 2)       ▼ (궤적 1000)
    (왼쪽으로 꺾기)    (직진 주행)      (오른쪽으로 꺾기)
        │                │                │
    [Critic 채점]    [Critic 채점]    [Critic 채점]
    - 벽과 충돌!      - 경로 잘 따름!   - 너무 돌아감
    👉 벌점: -1000점  👉 보상: +100점   👉 보상: +20점
        │                │                │
        └────────────────┼────────────────┘
                         ▼
        [가장 높은 점수를 받은 최적의 핸들 조향/속도 선택!] 
                         ▼
                    모터로 전송
```

1. **가상 주행 시뮬레이션 (Sampling):**  
   현재 위치에서 1,000가지의 가상 미래 경로를 앞쪽으로 2~3초간 무작위로 그려봅니다.
2. **보상/벌점 평가 (`Critics`):**  
   각각의 1,000개 궤적에 대해 Critic들이 점수를 매깁니다.
   * **장애물 근처로 감?** ➡️ `ObstaclesCritic`이 **강한 벌점(Penalty)** 부여
   * **플래너가 준 경로를 잘 따름?** ➡️ `PathAlignCritic`이 **높은 보상(Reward)** 부여
   * **후진 안 하고 앞으로 잘 감?** ➡️ `PreferForwardCritic`이 **보상** 부여
3. **실시간 경로 수정 (Path Integral):**  
   가장 높은 종합 점수(가장 낮은 Cost)를 얻은 궤적들을 조합하여 지금 당장 밟아야 할 액셀과 조향각(`cmd_vel`)을 모터에 보냅니다.

---

### 💡 일반 강화학습(RL)과 다른 점은?

* **일반 딥러닝 강화학습(PPO, SAC 등):**  
  수만 번의 사전 학습(Training)을 거쳐 신경망(Neural Network) 모델을 만들어야 합니다.
* **MPPI (Model Predictive):**  
  사전 학습 없이, 로봇의 물리 법칙(아커만 조향 기하학)을 바탕으로 **현장에서 실시간으로 미래를 수천 번 상상(시뮬레이션)해보고 가장 보상이 큰 행동을 즉석에서 결정**합니다.

> **결론:**  
> 네, 이해하신 내용이 정확합니다!  
> 플래너가 큰 길을 주면, 컨트롤러(MPPI)는 **강화학습의 보상/벌점 개념(Critic)**을 활용해 0.05초마다 수천 개의 미래를 내다보고 실시간으로 가장 안전하고 완벽한 주행 경로를 선택합니다.

---

## 🧑 사용자 (User) - Q11

현재 코드에 사용중인 RPP도 보상/벌점 아니야? 강화학습같은거 아닌가?

---

## 🤖 어시스턴트 (Antigravity)

**아닙니다! RPP는 보상/벌점이나 강화학습 방식이 아니라, 순수 "기하학 공식(Geometry) + 수학 규칙(Rule-based)"으로 움직이는 제어기입니다.**

두 알고리즘의 동작 방식 차이를 비유로 보시면 바로 이해가 되실 겁니다!

---

### 1. RPP (Regulated Pure Pursuit)의 작동 방식: 🥕 "당근 따라가기 기하학 공식"

RPP는 미래를 시뮬레이션하거나 여러 경로를 후보로 두고 채점하지 않습니다. **단 하나의 정해진 삼각함수 공식**으로 답을 한 번에 구합니다.

```
                      (1.5m 앞의 점: Lookahead Point) 🥕
                                                    ／
                                                  ／
                     (원호 궤적 곡선)           ／ 
                   ╭───────────────────────────╯
                   │
                [Hunter 로봇]
```

1. **Pure Pursuit (순수 추종):**  
   로봇 앞쪽 $1.5\text{m}$ 지점(`lookahead_dist`)의 경로 위에 **점(당근)**을 하나 찍습니다.
2. **삼각함수 공식 대입:**  
   "내 위치에서 저 점까지 가려면 핸들을 몇 도 꺾어야 하는가?"를 **기하학 원호 공식($\kappa = \frac{2\sin\alpha}{L}$)**에 대입해 **단 1개의 조향각을 즉시 계산**합니다.
3. **Regulated (속도 조절 규칙):**  
   단순한 수학적 규칙(Rule)으로 속도만 줄여줍니다:
   * *"커브가 심하네? ➡️ 속도를 $0.5$배로 줄여라."*
   * *"앞에 벽이 있네? ➡️ 정지해라."*

> 📌 **RPP의 특징:**  
> 여러 후보를 만들어 점수를 매기는 게 아니라, **$1+1=2$ 처럼 공식에 넣으면 딱 1개의 제어 명령이 나오는 방식**입니다. 연산량이 거의 없어 CPU를 거의 먹지 않고 매우 가볍고 안정적입니다.

---

### 2. MPPI vs RPP 한눈에 비교

| 비교 항목 | RPP (현재 사용 중) | MPPI |
| :--- | :--- | :--- |
| **방식** | **기하학 공식 (삼각함수)** | **확률적 샘플링 + 보상/벌점 (강화학습형)** |
| **미래 궤적 생성** | **1개** (공식에 의해 딱 정해진 곡선) | **1,000개 ~ 2,000개** (다양한 가상 미래 궤적) |
| **채점(Critic/Reward)**| ❌ 없음 (공식으로 계산) | ⭕ 있음 (각 궤적마다 점수를 매김) |
| **장애물 회피 능력** | 경로가 막히면 **그냥 멈춤** (플래너가 새 길을 줄 때까지 대기) | 컨트롤러가 스스로 **경로를 살짝 이탈해 우회**해서 지나감 |
| **연산량 (CPU)** | **매우 가벼움 (0.1% 미만)** | 무거움 (수천 개 궤적 계산) |

---

### 💡 파라미터에서 본 "벌점(Penalty)" 단어는 왜 있었을까요?

`nav2_params.yaml`에 있던 `reverse_penalty`, `cost_penalty` 같은 단어는 RPP가 아니라 **`planner_server` (SmacPlannerHybrid, A\* 길찾기)**에서 사용하는 비용 가중치입니다.

* **RPP:** "공식대로 선만 따라갈게!" (순수 추종)
* **MPPI:** "1,000가지 방법으로 가보고, 보상 점수 제일 높은 길로 갈게!" (강화학습형 최적 제어)

---

