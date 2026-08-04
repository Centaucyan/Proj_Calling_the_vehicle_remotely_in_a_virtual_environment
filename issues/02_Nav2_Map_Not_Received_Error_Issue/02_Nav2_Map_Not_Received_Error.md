# Issue 02: Nav2 실행 시 RViz2 지도가 안 뜨는 문제 (No map received)

## 🚨 문제 현상 (Issue Description)
- `ros2 launch hunter_gazebo bringup_sim_nav2.launch.py` 명령으로 시뮬레이션 및 Nav2를 실행했을 때, RViz2 상에서 지도가 보이지 않음.
- RViz2의 Map 디스플레이 상태창에 `No map received` 경고 발생.
- RViz2 Global Status에 `Fixed Frame [map] does not exist` 에러 발생.

## 🕵️ 원인 분석 (Root Cause)
이번 에러는 두 가지 원인이 겹쳐서 발생한 **복합적인 문제**로 확인되었습니다.

### 1. `behavior_server` 노드 누락 (라이프사이클 에러)
- ROS2 Humble의 Nav2 구조에서 경로 탐색(`bt_navigator`) 노드는 장애물 회피 등의 복구 동작을 수행하기 위해 `behavior_server` 노드를 필수로 요구함.
- `navigation.launch.py`와 `nav2_params.yaml`에 해당 노드가 누락되어 있어 `bt_navigator`가 켜지는 과정에서 에러가 발생함.
- 연쇄 작용으로 `nav2_lifecycle_manager`가 안전을 위해 이전에 켜두었던 `map_server`를 포함한 모든 노드를 강제로 비활성화(Deactivate) 시켜버림. (그 결과 `/map` 토픽이 발행되지 않음)

### 2. Launch 파일 전역 변수명 충돌 (`params_file`)
- `bringup_sim_nav2.launch.py`는 Gazebo와 Nav2를 동시에 포함(Include)하여 실행함.
- 하위로 실행되는 Gazebo의 런치 파일 시스템 내부에서 `params_file`이라는 전역 변수를 먼저 선언하고 빈 문자열(`''`)로 초기화함.
- 우연하게도 `navigation.launch.py` 역시 파라미터 파일 경로를 넘겨받기 위해 동일한 이름인 `params_file`을 사용함.
- 결과적으로 Gazebo의 '빈 문자열'이 Nav2의 변수에 덮어씌워져, Nav2 노드들이 `nav2_params.yaml`을 불러오지 못하는 대참사 발생.
- 파라미터가 비어있자 `controller_server`가 기본 컨트롤러(`DWBLocalPlanner`)를 억지로 사용하려다 `Couldn't load critics!` 에러를 뿜으며 완전히 시스템이 다운됨.

## 🛠️ 해결 방법 (Resolution)
위 두 가지 문제를 해결하기 위해 다음 2개 파일을 수정함.

### 수정 파일 1: `src/hunter_robot/hunter_gazebo/config/nav2_params.yaml`
- 파일 맨 아래에 `behavior_server` 관련 설정(plugin 등) 블록을 새롭게 추가함.
- `lifecycle_manager`의 `node_names` 리스트에 `'behavior_server'` 항목을 추가함.

### 수정 파일 2: `src/hunter_robot/hunter_gazebo/launch/navigation.launch.py`
- `behavior_server` 노드 실행(`Node(...)`) 코드를 추가함.
- `lifecycle_manager`의 `node_names` 파라미터 리스트에 `'behavior_server'` 항목을 추가함.
- **[변수명 충돌 해결]** Gazebo와의 충돌을 피하기 위해 파일 내에 선언된 `params_file` 이라는 이름을 모두 **`nav_params_file`** 로 일괄 변경함.

## ✅ 결과 (Result)
- `colcon build` 후 재실행 시 모든 Nav2 라이프사이클 노드들이 정상적으로 `Active` 상태로 전환됨.
- `map_server`가 정상적으로 `/map` 토픽을 발행하여 RViz2 화면에 지도가 성공적으로 출력됨.
