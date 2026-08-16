# 2026년 08월 16일 대화 기록 (Conversation History)

**작성일시:** 2026-08-16
**대화 주제:** Nav2 제어기(MPPI vs RPP) 트러블슈팅 및 튜닝 (장애물 회피 정지/교착 현상, Reeds-Shepp 후진 불가 및 타이어 흔들림, MPPI 속도 제한 원인 분석, RPP 고속 회전 시 라이다-2D 지도 틀어짐 보완 대책)

---

## 🧑 사용자 (User) - Q1

nav2_params.yaml 파일에서 FollowPath플러그인을 rpp에서 mppi로 변경 후 해보니 첨부 이미지와 같이 장애물들 사이에서 전진을 못하고 있다. 
ros2 topic echo /navigate_to_pose/_action/status
로 확인하면 여전히 status는 2로 자율주행 중이다.
파라미터 값을 뭐를 변경해보면 될까?
먼저 yaml 파일 확인 후 파일 수정하지 말고 나에게 먼저 알려줘~

---

## 🤖 어시스턴트 (Antigravity)

[`nav2_params.yaml`](file:///Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml) 파일을 분석했습니다. 요청하신 대로 **파일은 수정하지 않고**, 원인과 변경해야 할 핵심 파라미터를 정리해 드립니다.

---

### 1. 현상 분석: 왜 Status 2(주행 중)인데 전진을 못 하는가?

* `status: 2`는 `STATUS_EXECUTING` 상태로, **내비게이션 액션 자체는 실패(Abort)하지 않고 정상 동작 중**임을 의미합니다.
* 하지만 MPPI(Model Predictive Path Integral) 알고리즘 특성상 수천 개의 궤적을 가상으로 시뮬레이션할 때 **장애물 회피 벌점(Obstacle Cost)이 전진 보상(Path Follow Reward)보다 훨씬 커서**, 계산된 최적의 명령 속도($v$)가 **`0` 또는 정지에 가까운 극소값으로 수렴해 교착 상태(Deadlock / Local Minimum)**에 빠진 것입니다.

---

### 2. 주요 원인 및 변경 추천 파라미터

#### ① `ObstaclesCritic` 벌점 완화 (가장 직접적인 원인)
현재 장애물 근처에서 느끼는 반발력과 충돌 판정 여유가 너무 빡빡하여 좁은 통로로 들어가는 모든 궤적이 버려지고 있습니다.

* **`repulsion_weight: 1.5` $\rightarrow$ `0.3 ~ 0.5` 권장**
  * 장애물 주변 인플레이션 코스트 영역에 진입할 때 부여하는 벌점입니다. 좁은 통로를 통과하려면 인플레이션 구역을 지나갈 수밖에 없는데, 이 값이 크면 통로 진입 자체를 거부하고 멈춰 서게 됩니다.
* **`collision_margin_distance: 0.1` $\rightarrow$ `0.0 ~ 0.03` 권장**
  * 차체 외곽선(Footprint) 바깥으로 추가 안전 마진을 두는 설정입니다. 장애물 사이가 좁은 환경에서는 이 마진 때문에 가상 충돌로 판정(`collision_cost: 10000.0` 부과)되어 전진 궤적이 전멸합니다.

---

#### ② `local_costmap`의 인플레이션 설정 완화 (필수 연계 설정)
* **`inflation_layer.cost_scaling_factor: 2.0` $\rightarrow$ `5.0 ~ 8.0` 권장**
  * `cost_scaling_factor`가 2.0으로 작으면 장애물에서 멀어져도 위험도(Cost)가 천천히 줄어들어 **장애물 사이 통로 전체가 고위험 구역(Cost > 150)으로 가득 차게 됩니다.**
  * 값을 5.0 이상으로 높이면 벽 바로 옆에서만 Cost가 급격히 올라가고 통로 중앙은 안전한 저비용 구역이 형성되어 로봇이 지나갈 수 있습니다.
* **`inflation_layer.inflation_radius: 1.0` $\rightarrow$ `0.6 ~ 0.7` 권장**
  * 장애물 간격이 좁은 맵에서 반경이 1.0m이면 양쪽 장애물의 인플레이션 영역이 서로 겹쳐서 '막힌 벽'처럼 인식됩니다.

---

#### ③ Critic 간 가중치 밸런스 조정 (전진 추진력 강화)
* **`PathFollowCritic.cost_weight: 5.0` $\rightarrow$ `8.0 ~ 10.0` 권장**
  * 전역 경로(Global Path)를 따라 앞으로 나아가는(Progress) 것에 대한 보상을 올려주어, 장애물 반발력을 뚫고 전진하려는 추진력을 부여합니다.
* **`PathAlignCritic.cost_weight: 10.0` $\rightarrow$ `4.0 ~ 6.0` 권장**
  * 현재 경로 정렬 가중치가 10.0으로 너무 높습니다. 장애물을 살짝 비켜 가려는 궤적조차 "전역 경로와 어긋났다"는 이유로 큰 감점을 받아버려 결국 제자리에 서 있는 궤적이 선택됩니다.

---

#### ④ 탐색 다양성(Exploration) 확보
* **`vx_std: 0.2` $\rightarrow$ `0.3 ~ 0.4` 권장**
  * 로봇이 완전히 멈춰 있을 때 속도 샘플링 표준편차가 0.2로 작으면 생성되는 궤적들의 속도가 대부분 0 근처에 머물러 정지 상태를 탈출하기 어렵습니다.
* **`iteration_count: 1` $\rightarrow$ `2 ~ 3` 권장** (CPU 여유가 있다면)
  * 제어 주기당 MPPI 최적화 반복 횟수를 늘려 국소 최적해(0 속도)에서 전진 궤적으로 수렴할 기회를 높입니다.

---

### 3. 추천 변경 파라미터 요약 비교표

| 위치 | 파라미터 | 기존 값 | 추천 변경 값 | 목적 |
| :--- | :--- | :--- | :--- | :--- |
| **FollowPath.ObstaclesCritic** | `repulsion_weight` | `1.5` | **`0.4`** | 통로 진입 시 반발 벌점 완화 |
| **FollowPath.ObstaclesCritic** | `collision_margin_distance` | `0.1` | **`0.0`** 또는 **`0.02`** | 좁은 틈새 가상 충돌 방지 |
| **FollowPath.PathFollowCritic** | `cost_weight` | `5.0` | **`8.0`** | 전진 진행 보상 강화 |
| **FollowPath.PathAlignCritic** | `cost_weight` | `10.0` | **`5.0`** | 경로 정렬 집착 완화 |
| **FollowPath** | `vx_std` | `0.2` | **`0.35`** | 정지 탈출 샘플링 다양화 |
| **local_costmap.inflation_layer** | `cost_scaling_factor` | `2.0` | **`6.0`** | 통로 중앙 저비용 구역 확보 |
| **local_costmap.inflation_layer** | `inflation_radius` | `1.0` | **`0.6`** | 인플레이션 겹침 현상 방지 |

---

### 💡 디버깅 팁
1. `ros2 topic echo /cmd_vel`을 실행하여 현재 로봇에 발행되는 `linear.x` 속도가 0에 가깝게 나오는지 확인해 보세요.
2. `FollowPath`의 `visualize: true`로 설정하면 RViz에서 MPPI가 샘플링하는 궤적 후보군 토픽(`/controller_server/trajectories` 등)을 시각적으로 보면서 궤적들이 장애물에 막히는지 확인할 수 있습니다.

확인해 보시고, 위 파라미터들을 직접 수정하시거나 제가 수정해 드리길 원하시면 말씀해 주세요!

---

## 🧑 사용자 (User) - Q2

rviz2 띄울 때 아래 오류는 뭐지?

[ERROR] [1786889713.136408376] [rviz2]: Vertex Program:rviz/glsl120/indexed_8bit_image.vert Fragment Program:rviz/glsl120/indexed_8bit_image.frag GLSL link result : 
active samplers with a different type refer to the same texture image unit

---

## 🤖 어시스턴트 (Antigravity)

해당 오류는 RViz2에서 **Map(지도)**이나 **Costmap(비용 지도)** 같은 8비트 인덱스 이미지를 렌더링할 때 발생하는 **OpenGL 셰이더(GLSL)와 그래픽 드라이버 간의 충돌 메시지**입니다.

```text
[ERROR] [rviz2]: Vertex Program:rviz/glsl120/indexed_8bit_image.vert Fragment Program:rviz/glsl120/indexed_8bit_image.frag GLSL link result : 
active samplers with a different type refer to the same texture image unit
```

---

### 1. 원인이 무엇인가요?
* RViz2가 맵/코스트맵을 그리기 위해 내부 셰이더(`indexed_8bit_image`)를 컴파일하고 링크할 때, 서로 다른 타입의 텍스처 샘플러(Sampler)들이 동일한 GPU 텍스처 유닛(Texture Unit 0)을 참조하면서 OpenGL의 유효성 검사 규칙에 걸려 출력되는 메시지입니다.
* 주로 **Ubuntu 기본 Wayland 세션**, **Intel/Mesa 내장 그래픽 드라이버**, 또는 **ROS 2(Humble / Iron / Jazzy)의 RViz2 렌더링 파이프라인**에서 자주 나타나는 잘 알려진 OpenGL 이슈입니다.

---

### 2. 신경 써야 하는 문제인가요?
* **정상적으로 맵/로봇이 보인다면:** **무시하셔도 전혀 무방합니다.** (Non-fatal 경고성 오류)
  * RViz2가 꺼지거나 멈추지 않고 화면에 지도와 로봇이 잘 뜬다면, 자율주행 알고리즘(Nav2, MPPI)이나 로봇 제어 동작에는 **아무런 영향을 주지 않습니다.**
* **맵/Costmap이 검은색으로 나오거나 화면이 깨질 때:** 아래의 조치 방법을 적용해 볼 수 있습니다.

---

### 3. 해결 및 완화 방법 (렌더링 문제가 발생할 경우)

#### ① X11 (XCB) 플랫폼 강제 지정 (가장 흔한 해결법)
Ubuntu Wayland 세션 환경에서 발생하는 경우가 많으므로 터미널에서 X11 백엔드로 실행합니다:
```bash
export QT_QPA_PLATFORM=xcb
rviz2
```

#### ② 소프트웨어 렌더링으로 실행 (GPU 드라이버 충돌 우회)
GPU 하드웨어 가속과의 호환성 문제일 경우 소프트웨어 렌더러로 우회할 수 있습니다:
```bash
export LIBGL_ALWAYS_SOFTWARE=1
rviz2
```

#### ③ RViz2 Display 설정 변경
* RViz2 좌측 Displays 패널에서 `Map` 또는 `Costmap` 항목의 **`Color Scheme`**을 `map`, `costmap`, `raw` 등으로 변경해 보거나 껐다 켜보세요.

---

## 🧑 사용자 (User) - Q3

전진 후 후진으로 들어갈때 왜 끝까지 전진하지 않고, 지금 이미지처럼 저 위치에서 후진하려고 하지? 후진도 안해... 타이어만 좌우로 움직여...

---

## 🤖 어시스턴트 (Antigravity)

질문하신 두 가지 현상(**① 끝까지 전진하지 않고 중간에 멈추는 이유**, **② 후진도 안 하고 타이어만 좌우로 도리도리 움직이는 이유**)은 MPPI 컨트롤러의 **후진 관련 Critic 설정 충돌** 때문에 발생하는 전형적인 현상입니다.

원인과 해결 방법을 자세히 설명해 드리겠습니다.

---

### 1. 왜 이런 현상이 발생하나요?

#### 📌 원인 1: `PreferForwardCritic`이 후진을 원천 차단함 (결정적 원인)
* 플래너(SmacPlanner)는 장애물을 피하기 위해 **Reeds-Shepp(전진 $\rightarrow$ 변곡점 $\rightarrow$ 후진)** 경로를 생성했습니다.
* 하지만 MPPI의 `PreferForwardCritic`은 **"후진($v < 0$)하면 무조건 벌점 5.0 부과!"**하도록 켜져 있습니다.
* 컨트롤러 입장에서는 플래너가 후진하라고 시키는데, 후진을 하면 벌점이 너무 커지니 **최선의 선택으로 속도를 0($vx = 0$, 정지)으로 묶어버린 것**입니다.

#### 📌 원인 2: `PathAngleCritic`이 `mode: 0`(전진 전용)으로 설정됨
* 현재 `PathAngleCritic`의 `mode: 0`은 **"로봇 앞머리가 무조건 경로 방향과 일치해야 한다"**는 설정입니다.
* 후진 주행 시에는 로봇 뒷면이 진행 방향을 향해야 정상인데, `mode: 0` 상태에서는 이를 **$180^\circ$ 헤딩 에러**로 간주하여 엄청난 벌점을 매깁니다. (후진을 허용하려면 `mode: 1`로 해야 함)

#### 📌 원인 3: 왜 끝까지 안 가고 저 어정쩡한 위치에서 멈추는가? (미래 예측 시야 때문)
* MPPI는 현재 위치에서 미래 **2.8초**(`56 steps × 0.05s`) 앞의 궤적을 미리 내다봅니다.
* 전진 끝 지점(변곡점)에 가까워지면, MPPI의 시야 안에 이미 **후진해야 하는 경로 구간**이 들어옵니다.
* 이때 앞서 언급한 `PreferForwardCritic`과 `PathAngleCritic`의 **후진 벌점 폭탄**이 미리 감지되면서, *"더 전진하면 곧 후진을 해야 해서 벌점이 엄청나니, 차라리 지금 멈추는 게 이득이다"*라고 계산하여 변곡점에 다 도달하기도 전에 중간에 멈춰 서게 됩니다.

#### 📌 원인 4: 왜 후진은 안 하고 타이어만 좌우로 움직이는가?
* 선속도($vx$)는 벌점 때문에 `0`으로 봉쇄되었지만, 경로 각도와 위치를 맞추려는 Critic들은 여전히 작동 중입니다.
* 결국 MPPI가 벌점을 조금이라도 줄이기 위해 **선속도는 0으로 둔 채 조향각($wz$)만 좌우로 계속 비틀어 명령**을 내리고 있는 것입니다.
* 아커만 조향 차량은 전/후진 모터가 돌지 않으면 제자리에서 앞바퀴만 꺾이므로 사용자의 눈에는 타이어만 좌우로 움직이는 것으로 보이게 됩니다.

---

### 2. 해결 방법: 변경해야 할 파라미터

[`nav2_params.yaml`](file:///Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml)의 `FollowPath` 설정에서 아래 2가지를 수정해야 합니다.

#### 1) `PreferForwardCritic` 비활성화 (또는 critics 목록에서 제거)
후진 기어를 넣어야 하는 아커만 자율주행에서는 후진 억제 벌점을 꺼야 합니다.
```yaml
      PreferForwardCritic:
        enabled: false                # 👈 true에서 false로 변경 (후진 허용)
        cost_power: 1
        cost_weight: 5.0
        threshold_to_consider: 0.5
```

#### 2) `PathAngleCritic`을 양방향(`mode: 1`)으로 변경
후진 시 로봇의 뒷방향 헤딩($180^\circ$)도 정상 경로 정렬로 인정하도록 설정합니다.
```yaml
      PathAngleCritic:
        enabled: true
        cost_power: 1
        cost_weight: 2.0
        offset_from_furthest: 4
        mode: 1                      # 👈 0(전진 전용)에서 1(전진/후진 양방향 허용)로 변경!
        threshold_to_consider: 0.5
```

#### 3) (선택 권장) `prune_distance` 축소
전진 변곡점을 지난 후 이미 지나온 전진 경로를 더 빨리 삭제하여 후진 경로에 빠르게 집중하도록 돕습니다.
```yaml
      prune_distance: 0.8            # 👈 기존 1.5에서 0.8로 축소 권장
```

---

### 3. 변경 요약

| 파라미터 | 기존 값 | 변경할 값 | 이유 |
| :--- | :--- | :--- | :--- |
| **`PreferForwardCritic.enabled`** | `true` | **`false`** | 후진 주행에 벌점을 주지 않도록 해제 |
| **`PathAngleCritic.mode`** | `0` | **`1`** | 후진 시 $180^\circ$ 반대 헤딩도 정상 각도로 인정 |
| **`prune_distance`** | `1.5` | **`0.8 ~ 1.0`** | 전진 완료 후 지나간 경로 빠른 정리 |

위 항목들을 적용하면 로봇이 전진 지점 끝까지 주행한 후, 앞바퀴를 꺾고 부드럽게 후진으로 진입할 수 있습니다.

---

## 🧑 사용자 (User) - Q4

경로 주행 시 차량이 너무 느려 vx_max를 2.5로 높였다. 그런데도 여전히 느려 ros2 topic echo /cmd_vel 하면 leaner x값이 0.8 이정도로 나오는데 왜그렇지?

---

## 🤖 어시스턴트 (Antigravity)

`vx_max: 2.5`로 설정했음에도 `linear.x`가 0.8 m/s 정도로 나오는 이유는, `vx_max`가 **"무조건 이 속도로 달려라"**가 아니라 **"아무리 빨라도 넘지 말아야 할 상한선"**이기 때문입니다.

MPPI는 미래 궤적을 가상으로 시뮬레이션하여 **"경로를 이탈하지 않고 장애물에 부딪히지 않는 가장 안전하고 최적화된 속도"**를 스스로 계산하는데, 현재 환경과 파라미터 조합에서는 **0.8 m/s 안팎이 가장 벌점(Cost)이 적은 속도로 계산**되고 있는 것입니다.

구체적인 원인 4가지와 속도를 올리는 방법을 설명해 드립니다.

---

### 1. 왜 0.8 m/s로 제한되는가? (주요 원인)

#### 📌 원인 1: 좁은 장애물 간격과 긴 미래 예측 시야 (가장 결정적)
* 현재 MPPI는 **2.8초 앞**(`56 time_steps × 0.05s`)의 미래를 내다보고 주행합니다.
* 만약 $v = 2.5\text{ m/s}$로 달리면 2.8초 동안 무려 **7.0m** 앞까지 궤적을 뻗게 됩니다.
* 하지만 현재 맵은 장애물들이 2~3m 간격으로 촘촘히 배치되어 있습니다. 
* 2.5 m/s로 뻗은 가상 궤적들은 **2~3초 뒤에 다음 장애물이나 벽에 무조건 충돌(`ObstaclesCritic` 벌점 폭탄)**하게 됩니다.
* 결국 충돌하지 않고 살아남는 궤적은 **속도를 0.8 m/s 수준으로 낮춰 2~3m 안에서 멈추거나 피할 수 있는 궤적뿐**이므로 이 속도가 선택됩니다.

#### 📌 원인 2: 아커만 조향 기구학 및 각속도 한계 (`wz_max: 1.0`)
* 아커만 차량이 곡선 경로(반경 $R$)를 돌 때 필요한 각속도는 $w = \frac{v}{R}$ 입니다.
* 로봇의 최소 회전 반경이 $R = 1.6\text{m}$일 때, $v = 2.5\text{ m/s}$로 코너를 돌려면 필요한 각속도는:
  $$w = \frac{2.5}{1.6} \approx 1.56\text{ rad/s}$$
* 하지만 현재 **`wz_max`가 `1.0 rad/s`로 제한**되어 있습니다. 
* 즉, 2.5 m/s로 달리면 코너를 돌지 못하고 언더스티어가 발생해 경로 밖으로 튕겨 나가게 되므로, MPPI는 `wz_max: 1.0` 안에서 경로를 벗어나지 않고 돌 수 있는 속도($v \le 1.0 \times 1.6 = 1.6\text{ m/s}$ 이하, 여유 마진 포함 약 0.8~1.0 m/s)로 감속합니다.

#### 📌 원인 3: 속도 샘플링 표준편차(`vx_std: 0.2`)가 너무 작음
* `vx_std: 0.2`는 현재 주행 속도 주변에서 $\pm 0.2 \sim 0.4\text{ m/s}$ 범위의 속도 후보군만 뽑아서 테스트한다는 뜻입니다.
* 출발(0 m/s)이나 저속 상태에서 1.5~2.5 m/s 같은 고속 후보군 자체가 가상 시뮬레이션에 잘 들어오지 않아 가속도가 매우 느려집니다.

#### 📌 원인 4: 경로 정렬 집착 (`PathAlignCritic`)
* 차가 빨리 달릴수록 관성으로 인해 전역 경로(Global Path) 중심선에서 좌우로 흔들리는 오차(Tracking Error)가 커집니다.
* MPPI는 경로 중심을 칼같이 따라가기 위해 스스로 속도를 줄여 정밀 주행을 선택합니다.

---

### 2. 속도를 더 시원하게 올리려면? (추천 파라미터 튜닝)

장애물 구간을 통과하거나 직선 구간에서 더 빠른 속도를 내게 하려면 아래 값들을 조절해 보세요.

| 파라미터 | 기존 값 | 추천 변경 값 | 효과 |
| :--- | :--- | :--- | :--- |
| **`vx_std`** | `0.2` | **`0.4 ~ 0.5`** | 고속 궤적 후보군을 더 적극적으로 탐색·샘플링함 |
| **`time_steps`** | `56` | **`35 ~ 40`** | 미래 시야를 약 1.8~2.0초(4~5m)로 줄여, 먼 미래 장애물 때문에 지레 겁먹고 감속하는 현상 완화 |
| **`wz_max`** | `1.0` | **`1.5 ~ 2.0`** | 코너에서도 감속을 덜 하고 빠른 조향으로 돌아나가도록 허용 (로봇 조향 스펙 허용 시) |
| **`PathFollowCritic.cost_weight`** | `10.0` | **`15.0`** | "경로를 따라 앞으로 빠르게 진도를 나가라"는 보상(추진력)을 더 크게 부여 |
| **`PathAlignCritic.cost_weight`** | `6.0` | **`3.0 ~ 4.0`** | 경로 중심선에서 약간 벗어나더라도 고속 주행을 용인함 |

> **💡 요약 가이드**
> 1. 먼저 **`vx_std: 0.4`**와 **`time_steps: 40`**으로 수정해 보세요. 먼 미래 장애물에 대한 과도한 방어 감속이 풀리면서 속도가 눈에 띄게 올라갈 것입니다.
> 2. 코너링 구간에서도 속도를 유지하고 싶다면 **`wz_max`를 1.5** 정도로 올려주시면 좋습니다.

---

## 🧑 사용자 (User) - Q5

mppi보다 rpp가 나은것 같아서 rpp로 돌리고 최고 속도를 2.0으로 올렸다. 
속도가 높아 차량이 회전 시 라이다와 2d 지도가 너무 많이 틀어진다. 
이것에 대해 보완할 방법이 없을까?

---

## 🤖 어시스턴트 (Antigravity)

고속 주행($2.0\text{ m/s} \approx 7.2\text{ km/h}$) 상태에서 회전할 때 라이다(Scan)와 2D 지도가 심하게 틀어지는 현상은 **"고속 코너링 시 발생하는 물리적 바퀴 미끄러짐(Tire Slip)과 AMCL 위치 추정의 지연(Lag)"** 때문에 발생합니다.

실제 차량이나 자율주행 로봇에서도 **직선 속도는 2.0 m/s로 유지하되, 회전 시의 틀어짐을 완벽히 방지하고 보정하는 4가지 단계별 해결책**을 제시해 드립니다.

---

### 1. 근본 원인: 왜 회전할 때만 라이다와 맵이 틀어지는가?

1. **원심력으로 인한 바퀴 미끄러짐 (Wheel Odometry 오차 폭발)**
   * 시뮬레이션(Gazebo)이나 실제 로봇이 2.0 m/s로 급커브를 돌면 강한 횡가속도($a = \frac{v^2}{R}$) 때문에 타이어가 옆으로 미끄러집니다.
   * 바퀴 엔코더(Odometry)는 "미끄러짐 없이 정직하게 회전했다"고 가정하고 계산하므로, **`odom` 좌표계 자체가 순식간에 수십 cm ~ 수십 도 틀어져 버립니다.**
2. **AMCL 파티클 필터의 추종 지연 (Lag)**
   * 2.0 m/s는 1초에 2m를 이동하는 매우 빠른 속도입니다. AMCL이 라이다 데이터를 지도와 매칭하여 위치를 보정하는 주기보다 **오도메트리가 틀어지는 속도가 훨씬 빠르면** 라이다 포인트가 맵에서 튕겨져 나가게 됩니다.

---

### 2. 해결 방법 (우선순위별 권장 가이드)

---

#### 🥇 1단계: RPP의 '곡률 기반 자동 감속' 활성화 (가장 즉각적이고 현실적인 해결책)
실제 자동차도 코너를 돌 때는 속도를 줄이듯이, **"직선에서는 2.0 m/s로 쏘고, 코너(곡선) 구간에서만 0.6~0.8 m/s로 안전하게 감속"**하도록 설정합니다. 코너를 빠져나오면 즉시 2.0 m/s로 재가속합니다.

[`nav2_params.yaml`](file:///Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml)의 `FollowPath`에서 아래 3개 파라미터를 수정합니다:

```yaml
    FollowPath:
      plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"
      desired_linear_vel: 2.0
      ...
      # 👇 false에서 true로 켜기 (커브에서 미끄러짐 방지용 자동 감속)
      use_regulated_linear_velocity_scaling: true

      # 👇 로봇의 최소 회전반경(1.6m) 기준 감속 시작 임계 반경
      regulated_linear_scaling_min_radius: 1.6

      # 👇 급커브를 돌 때 내려갈 최저 속도 (미끄러지지 않는 안전 속도: 0.6 ~ 0.8 m/s)
      regulated_linear_scaling_min_speed: 0.7
```
> **효과:** 직선 주로에서는 최고 속도(2.0 m/s)를 온전히 누리면서, 코너링 시 횡슬립이 사라져 라이다-맵 일치도가 즉시 안정화됩니다.

---

#### 🥈 2단계: AMCL 위치 추정 주기 및 라이다 빔 개수 상향
고속 회전 중에도 AMCL이 빠르게 위치를 갱신하고 정확하게 매칭할 수 있도록 파라미터를 강화합니다.

[`nav2_params.yaml`](file:///Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws/src/hunter_robot/hunter_gazebo/config/nav2_params.yaml)의 `amcl` 섹션:

```yaml
amcl:
  ros__parameters:
    use_sim_time: True
    # 👇 더 짧은 이동/회전마다 즉각 위치 재추정 (기존 0.1 -> 0.05)
    update_min_d: 0.05
    update_min_a: 0.05

    # 👇 맵 매칭에 사용하는 라이다 광선 수 증가 (기본 60개 -> 180개로 올려 정밀도 대폭 향상)
    max_beams: 180

    # 👇 순간 오차가 크게 벌어져도 맵 벽을 찾아 매칭할 수 있는 최대 거리 확대 (기본 2.0m -> 3.5m)
    laser_likelihood_max_dist: 3.5

    # 파티클 수 유지
    min_particles: 500
    max_particles: 2000
```

---

#### 🥉 3단계: RPP 조향 급조작 방지 (`lookahead_dist` 최적화)
시선을 너무 가까이 두면 코너 진입 시 핸들을 홱 꺾어 급격한 슬립이 발생합니다. 시선을 살짝 멀리 두어 부드러운 호를 그리며 진입하도록 유도합니다.

```yaml
    FollowPath:
      lookahead_dist: 1.2           # (기존 1.0 -> 1.2로 상향)
      min_lookahead_dist: 0.8       # (기존 0.7 -> 0.8로 상향)
      max_lookahead_dist: 2.5       # 고속 주행 시 더 멀리 바라봄
      lookahead_time: 1.5
```

---

#### 🛠️ 4단계 (추가 보완): Gazebo 바퀴 마찰력(Friction) 확인 및 EKF
만약 Gazebo 시뮬레이션 상에서 바퀴가 얼음판처럼 미끄러진다면:
1. **URDF/SDF 바퀴 마찰계수**: 로봇의 바퀴 링크 충돌 파라미터에서 `<mu1>1.0</mu1>`, `<mu2>1.0</mu2>` (또는 1.5)로 접지력을 올려주면 물리적인 헛돌림/슬립이 크게 줄어듭니다.
2. **IMU 센서 융합 (`robot_localization` EKF)**: 바퀴 오도메트리(`odom`)에 IMU 자이로 센서를 EKF로 융합하면, 바퀴가 미끄러져도 IMU가 실제 회전각을 정확히 잡아주어 TF가 틀어지지 않습니다.

---

### 💡 적용 권장 순서
1. **1단계(`use_regulated_linear_velocity_scaling: true`)**와 **2단계(AMCL 파라미터)**만 적용해도 고속 코너링 시 라이다가 맵에서 벗어나는 현상이 바로 잡힙니다.

---

