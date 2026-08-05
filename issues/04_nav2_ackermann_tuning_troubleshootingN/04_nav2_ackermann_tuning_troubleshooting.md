# Nav2 아커만(Ackermann) 조향 튜닝 및 주행 트러블슈팅 기록

## 1. AMCL 위치 추정 발산 현상 및 파라미터 최적화
* **현상:** 회전 시 로봇의 위치(라이다 빨간 점)와 지도(검은 선)가 심하게 틀어지거나 발산하는 문제 발생.
* **원인 및 조치:** 오도메트리와 라이다 센서 사이의 신뢰도 밸런스를 맞추기 위해 사용자 커스텀 튜닝 진행. 극단적인 값(0.8 등) 대신 적절한 노이즈 예상치 부여.
* **적용 파라미터:** 
  * `alpha1` ~ `alpha5`: `0.2` (미끄러짐 및 회전 오차 적정 수준 반영)
  * `update_min_d`: `0.1`, `update_min_a`: `0.1` (주행 및 회전 시 즉각적인 보정)
* **필수 조치:** 주행 전 반드시 `2D Pose Estimate`를 사용해 라이다와 지도를 완벽히 일치시키고 출발해야 함.

## 2. 후진 경로(3-point turn)를 무시하고 멈추는 현상
* **현상:** 플래너가 후진이 포함된 경로를 생성해도 로봇이 주행을 거부함.
* **원인:** 
  1. 전역 플래너가 오직 전진만 가능한 곡선 모델(`DUBIN`)을 사용하고 있었음.
  2. 주행 컨트롤러(`RegulatedPurePursuitController`)에 안전을 위한 **후진 금지**가 기본값으로 설정되어 있었음.
* **적용 파라미터:** 
  * `planner_server` (SmacPlannerHybrid): `motion_model_for_search: "REEDS_SHEPP"` (전후진 모두 가능한 곡선 모델로 변경)
  * `controller_server` (FollowPath): `allow_reversing: true` (후진 주행 허용)

## 3. 주행 중 가다 서기를 반복하는 현상 (Stuttering)
* **현상:** 주행 중 불필요하게 브레이크를 반복하며 덜컹거림.
* **원인:** 커브길이나 장애물 근처에서 안전을 위해 속도를 줄이는 자동 감속 기능이 너무 예민하게 작동함.
* **적용 파라미터 (`FollowPath`):** 
  * `use_regulated_linear_velocity_scaling: false`
  * `use_cost_regulated_linear_velocity_scaling: false`

## 4. 경로 계획(Planning) 시간이 1분 이상 걸리다 실패(status 6)하는 현상
* **현상:** 탁 트인 공간에서도 목적지까지의 경로를 계산하지 못하고 계속 재시도하다 최종 실패함.
* **원인:** 플래너의 최대 계산 횟수(`max_iterations`)가 `1000`으로 실수로 축소되어 있어, 복잡한 경로를 계산하기도 전에 포기해버림.
* **적용 파라미터 (`SmacPlannerHybrid`):** 
  * `max_iterations: 1000000` (계산 횟수 대폭 증가로 복구)
  * `minimum_turning_radius: 1.6`, `cost_penalty: 6.0` (맵 환경과 로봇의 물리적 조향 반경을 고려한 최적값 적용)

## 5. 진짜 벽(라이다 점)을 무시하고 부딪히며 멈추는 현상 (물리적 갇힘)
* **현상:** 로봇이 물리적인 장애물(빨간 점)을 피하지 않고 진입하다가 코앞에서 급정거하여 갇혀버림.
* **원인:** AMCL 위치 틀어짐(Drift)으로 인해 '가짜 벽(검은 선)'과 '진짜 벽(빨간 점)'이 어긋남. 라이다 시야 제한(`obstacle_range: 2.5m`) 때문에 멀리서는 전역 플래너가 진짜 벽을 보지 못하고 가짜 벽을 기준으로 경로를 짬. 가까이 가서야 진짜 벽을 발견한 컨트롤러가 충돌 방지(`use_collision_detection: true`)를 발동해 멈춰버림.
* **해결 방안:** 
  1. 가장 근본적인 해결책은 주행 전 `2D Pose Estimate`로 맵과 라이다를 포개어 위치 틀어짐을 없애는 것임.
  2. 물리적으로 완전히 갇혔을 때는 수동 조종(Teleop)을 이용해 로봇을 빈 공간으로 빼내어 위치를 갱신시켜야 함. (향후 행동 트리(BT)에 `DriveOnHeading` 등의 커스텀 탈출 로직 추가 고려 가능)

## 6. 부드러운 스티어링 유도 및 코스트맵 일치 (주행 최적화)
* **전방 주시 거리(Lookahead) 조절:** 바퀴 미끄러짐(Slip)을 막기 위해 시선을 멀리 두고 부드럽게 핸들을 꺾도록 튜닝.
  * `min_lookahead_dist: 0.7`, `lookahead_dist: 1.0`, `max_lookahead_dist: 2.0`
* **코스트맵 통합:** `local_costmap`과 `global_costmap`의 장애물 방어막(Inflation) 설정을 완벽히 동일하게 맞춰 플래너와 컨트롤러 간의 인지 차이 해소.
  * `inflation_radius: 1.0`, `cost_scaling_factor: 2.0`
