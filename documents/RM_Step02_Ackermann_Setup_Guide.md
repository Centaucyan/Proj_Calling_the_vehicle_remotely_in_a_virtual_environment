# 2단계: 아커만 조향(Ackermann Steering) 신규 로봇 모델 구축 및 경량 월드 설정 가이드

본 문서는 기존 차동 구동(Diff Drive) 대신 실제 승용차 형태의 **4륜 아커만 조향(Ackermann Steering)** 로봇 모델(`ackermann.urdf.xacro`)과 컨트롤러를 신규 추가하고, 저사양 개발 환경을 고려한 **경량 회색 격자 월드(`default.world`)** 설정 및 Gazebo 검증을 수행하는 상세 가이드입니다.

---

## 1. 신규 및 수정 대상 파일 개요

1. **[컨트롤러 정의 파일]** `linorobot2_description/urdf/controllers/ackermann_drive.urdf.xacro` [신규 추가]
   - Gazebo에서 앞바퀴 조향(Steering Hinge) 및 4륜 구동을 제어하는 `gazebo_ros_ackermann_drive` 플러그인 설정
2. **[로봇 모델 정의 파일]** `linorobot2_description/urdf/robots/ackermann.urdf.xacro` [신규 추가]
   - 4륜 차체 구조, 전륜 조향 힌지/조인트 2개, 휠 4개, 3D-LiDAR, 카메라 센서를 통합한 완성형 URDF 정의
3. **[경량 월드 정의 파일]** `linorobot2_gazebo/worlds/default.world` [신규 추가]
   - 고용량 놀이터(`playground.world`) 대신 시뮬레이션 부하를 최소화하는 기본 회색 격자 무늬 바닥 및 조명 설정
4. **[시뮬레이션 런치 파일]** `linorobot2_gazebo/launch/gazebo.launch.py` [수정]
   - ROS2 Humble 런치 파라미터 파싱 문제 해결(`ParameterValue`) 및 기본 실행 월드를 `default.world`로 변경

---

## 2. 파일별 코드 상세 내용

### ① `linorobot2_description/urdf/controllers/ackermann_drive.urdf.xacro` [신규 추가]

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://ros.org/wiki/xacro">
  <xacro:macro name="ackermann_drive" params="wheel_diameter wheel_base wheel_separation max_steer_angle">
    <gazebo>
      <plugin name="ackermann_drive" filename="libgazebo_ros_ackermann_drive.so">
        <ros>
          <remapping>cmd_vel:=/cmd_vel</remapping>
          <remapping>odom:=/odom</remapping>
        </ros>

        <update_rate>100.0</update_rate>

        <!-- 필수 조향 조인트 2개 -->
        <left_steering_joint>front_left_steer_joint</left_steering_joint>
        <right_steering_joint>front_right_steer_joint</right_steering_joint>

        <!-- 필수 구동 바퀴 조인트 2개 -->
        <left_joint>rear_left_wheel_joint</left_joint>
        <right_joint>rear_right_wheel_joint</right_joint>

        <!-- 제원 및 구동 토크 파라미터 -->
        <max_steer>${max_steer_angle}</max_steer>
        <max_steer_rate>2.0</max_steer_rate>
        <max_speed>20.0</max_speed>
        <max_torque>500.0</max_torque>

        <!-- PID 게인 파라미터 -->
        <left_steering_pid_gain>1500 0 1</left_steering_pid_gain>
        <left_steering_i_limit>0 0</left_steering_i_limit>
        <right_steering_pid_gain>1500 0 1</right_steering_pid_gain>
        <right_steering_i_limit>0 0</right_steering_i_limit>
        <linear_velocity_pid_gain>1000 0 1</linear_velocity_pid_gain>
        <linear_velocity_i_limit>0 0</linear_velocity_i_limit>

        <wheel_separation>${wheel_separation}</wheel_separation>
        <wheel_diameter>${wheel_diameter}</wheel_diameter>

        <!-- 오도메트리 퍼블리시 설정 -->
        <publish_odom>true</publish_odom>
        <publish_odom_tf>true</publish_odom_tf>
        <publish_wheel_tf>true</publish_wheel_tf>
        <odometry_frame>odom</odometry_frame>
        <robot_base_frame>base_footprint</robot_base_frame>
      </plugin>
    </gazebo>
  </xacro:macro>
</robot>
```

---

### ② `linorobot2_description/urdf/robots/ackermann.urdf.xacro` [신규 추가]

```xml
<?xml version="1.0"?>
<robot name="linorobot2_ackermann" xmlns:xacro="http://ros.org/wiki/xacro">
  <!-- 차체 및 휠 제원 정의 -->
  <xacro:property name="base_length" value="0.5" />
  <xacro:property name="base_width" value="0.3" />
  <xacro:property name="base_height" value="0.1" />
  <xacro:property name="base_mass" value="10" />

  <xacro:property name="wheel_radius" value="0.08" />
  <xacro:property name="wheel_width" value="0.04" />
  <xacro:property name="wheel_pos_x" value="0.18" />  <!-- 휠베이스(전장) 오프셋 -->
  <xacro:property name="wheel_pos_y" value="0.18" />  <!-- 윤거(트레드) 오프셋 -->
  <xacro:property name="wheel_pos_z" value="-0.05" />
  <xacro:property name="wheel_mass" value="0.5" />
  <xacro:property name="max_steer_angle" value="0.523599" /> <!-- 최대 조향각 약 30도 -->

  <!-- 기본 모듈 및 센서 인클루드 -->
  <xacro:include filename="$(find linorobot2_description)/urdf/mech/base.urdf.xacro" />
  <xacro:include filename="$(find linorobot2_description)/urdf/mech/wheel.urdf.xacro" />
  <xacro:include filename="$(find linorobot2_description)/urdf/sensors/imu.urdf.xacro" />
  <xacro:include filename="$(find linorobot2_description)/urdf/sensors/generic_laser.urdf.xacro" />
  <xacro:include filename="$(find linorobot2_description)/urdf/sensors/depth_sensor.urdf.xacro" />
  <xacro:include filename="$(find linorobot2_description)/urdf/controllers/ackermann_drive.urdf.xacro" />

  <!-- 센서 배치 설정 -->
  <xacro:property name="laser_pose">
    <origin xyz="0.15 0 0.2" rpy="0 0 0"/>
  </xacro:property>
  <xacro:property name="depth_sensor_pose">
    <origin xyz="0.2 0 0.15" rpy="0 0 0"/>
  </xacro:property>

  <!-- 1. 메인 차체 생성 -->
  <xacro:base length="${base_length}" width="${base_width}" height="${base_height}" mass="${base_mass}" wheel_radius="${wheel_radius}" wheel_pos_z="${wheel_pos_z}" />

  <!-- 2. 후륜 2개 (구동 바퀴) 생성 -->
  <xacro:wheel 
    side="rear_left" 
    radius="${wheel_radius}" 
    width="${wheel_width}" 
    pos_x="${-wheel_pos_x}" 
    pos_y="${wheel_pos_y}" 
    pos_z="${wheel_pos_z}" 
    mass="${wheel_mass}" 
  />
  <xacro:wheel 
    side="rear_right" 
    radius="${wheel_radius}" 
    width="${wheel_width}" 
    pos_x="${-wheel_pos_x}" 
    pos_y="${-wheel_pos_y}" 
    pos_z="${wheel_pos_z}" 
    mass="${wheel_mass}" 
  />

  <!-- 후륜 구동 바퀴 지면 마찰력(Traction) 설정 -->
  <gazebo reference="rear_left_wheel_link">
    <mu1>100.0</mu1>
    <mu2>100.0</mu2>
    <kp>10000000.0</kp>
    <kd>1.0</kd>
  </gazebo>
  <gazebo reference="rear_right_wheel_link">
    <mu1>100.0</mu1>
    <mu2>100.0</mu2>
    <kp>10000000.0</kp>
    <kd>1.0</kd>
  </gazebo>

  <!-- 3. 전륜 2개 (조향 힌지 + 바퀴) 생성 매크로 -->
  <xacro:macro name="front_steer_wheel" params="side pos_x pos_y pos_z">
    <!-- 조향 힌지 링크 (Gazebo 조인트 트리 정상화용 형상 및 관성 정의) -->
    <link name="${side}_steer_link">
      <visual>
        <origin xyz="0 0 0" rpy="0 0 0"/>
        <geometry>
          <box size="0.02 0.02 0.02"/>
        </geometry>
        <material name="black">
          <color rgba="0.1 0.1 0.1 1.0"/>
        </material>
      </visual>
      <inertial>
        <origin xyz="0 0 0" rpy="0 0 0"/>
        <mass value="0.1"/>
        <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/>
      </inertial>
    </link>

    <!-- 조향 힌지 조인트 (Z축 회전: 좌우 조향) -->
    <joint name="${side}_steer_joint" type="revolute">
      <parent link="base_link"/>
      <child link="${side}_steer_link"/>
      <origin xyz="${pos_x} ${pos_y} ${pos_z}" rpy="0 0 0"/>
      <axis xyz="0 0 1"/>
      <limit lower="-${max_steer_angle}" upper="${max_steer_angle}" effort="10.0" velocity="5.0"/>
    </joint>

    <!-- 전륜 바퀴 링크 -->
    <link name="${side}_wheel_link">
      <visual>
        <origin xyz="0 0 0" rpy="${pi/2} 0 0"/>
        <geometry>
          <cylinder radius="${wheel_radius}" length="${wheel_width}"/>
        </geometry>
        <material name="blue">
          <color rgba="0.1764 0.4588 0.8509 1.0"/>
        </material>
      </visual>
      <collision>
        <origin xyz="0 0 0" rpy="${pi/2} 0 0"/>
        <geometry>
          <cylinder radius="${wheel_radius}" length="${wheel_width}"/>
        </geometry>
      </collision>
      <inertial>
        <origin xyz="0 0 0" rpy="0 0 0"/>
        <mass value="${wheel_mass}"/>
        <inertia ixx="${(2/5) * wheel_mass * (wheel_radius * wheel_radius)}" ixy="0" ixz="0"
                 iyy="${(2/5) * wheel_mass * (wheel_radius * wheel_radius)}" iyz="0"
                 izz="${(2/5) * wheel_mass * (wheel_radius * wheel_radius)}" />
      </inertial>
    </link>

    <gazebo reference="${side}_wheel_link">
      <material>Gazebo/Blue</material>
      <mu1>100.0</mu1>
      <mu2>100.0</mu2>
      <kp>10000000.0</kp>
      <kd>1.0</kd>
    </gazebo>

    <!-- 전륜 바퀴 회전 조인트 -->
    <joint name="${side}_wheel_joint" type="continuous">
      <parent link="${side}_steer_link"/>
      <child link="${side}_wheel_link"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <axis xyz="0 1 0"/>
      <limit effort="100.0" velocity="100.0"/>
    </joint>
  </xacro:macro>

  <!-- 전륜 좌/우 바퀴 인스턴스 생성 -->
  <xacro:front_steer_wheel side="front_left" pos_x="${wheel_pos_x}" pos_y="${wheel_pos_y}" pos_z="${wheel_pos_z}" />
  <xacro:front_steer_wheel side="front_right" pos_x="${wheel_pos_x}" pos_y="${-wheel_pos_y}" pos_z="${wheel_pos_z}" />

  <!-- 4. 센서 및 아커만 플러그인 로드 -->
  <xacro:imu/>
  <xacro:generic_laser><xacro:insert_block name="laser_pose" /></xacro:generic_laser>
  <xacro:depth_sensor><xacro:insert_block name="depth_sensor_pose" /></xacro:depth_sensor>

  <xacro:ackermann_drive 
    wheel_diameter="${wheel_radius * 2}" 
    wheel_base="${wheel_pos_x * 2}" 
    wheel_separation="${wheel_pos_y * 2}" 
    max_steer_angle="${max_steer_angle}" 
  />

  <gazebo>
    <plugin name="gazebo_ros_joint_state_publisher" filename="libgazebo_ros_joint_state_publisher.so">
      <update_rate>30</update_rate>
      <joint_name>front_left_steer_joint</joint_name>
      <joint_name>front_right_steer_joint</joint_name>
      <joint_name>front_left_wheel_joint</joint_name>
      <joint_name>front_right_wheel_joint</joint_name>
      <joint_name>rear_left_wheel_joint</joint_name>
      <joint_name>rear_right_wheel_joint</joint_name>
    </plugin>
  </gazebo>
</robot>
```

---

### ③ `linorobot2_gazebo/worlds/default.world` [신규 추가]

```xml
<?xml version="1.0" ?>
<sdf version="1.5">
  <world name="default">
    <!-- 기본 태양광 조명 -->
    <include>
      <uri>model://sun</uri>
    </include>
    <!-- 기본 회색 격자무늬 바닥 -->
    <include>
      <uri>model://ground_plane</uri>
    </include>
  </world>
</sdf>
```

---

### ④ `linorobot2_gazebo/launch/gazebo.launch.py` [수정]

```python
    # 33~35라인: 기본월드를 default.world(회색 격자)로 변경
    world_path = PathJoinSubstitution(
        [FindPackageShare("linorobot2_gazebo"), "worlds", "default.world"]
    )
```

---

## 3. 적용 및 실행 명령어

작성된 파일들을 바탕으로 빌드 및 시뮬레이션을 구동합니다.

```bash
# 1. ROS2 워크스페이스 이동 및 패키지 빌드
cd ~/Tae_ws/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws
colcon build --packages-select linorobot2_description linorobot2_gazebo
source install/setup.bash

# 2. 아커만 지정 및 해외 모델 데이터베이스 접속 차단 설정 후 구동
export LINOROBOT2_BASE=ackermann
export GAZEBO_MODEL_DATABASE_URI=""
ros2 launch linorobot2_gazebo gazebo.launch.py
```

---

## 4. 검증 및 테스트 상세 가이드

시뮬레이션이 켜진 후, **새 터미널**을 열어 아래 검증 항목들을 순서대로 수행합니다.

### 4.1 키보드 조종을 통한 앞바퀴 조향 및 주행 검증
```bash
# 새로운 터미널에서 키보드 조종 노드 실행
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
* **조작 키 안내:**
  * `i`: 전진 / `,`: 후진 / `k`: 정지
  * `j`: 좌회전 (전륜 앞바퀴가 왼쪽으로 꺾임)
  * `l`: 우회전 (전륜 앞바퀴가 오른쪽으로 꺾임)
* **검증 사항:** Gazebo 화면에서 차량 이동 시 앞바퀴 2개가 곡선 궤적에 맞춰 좌우로 물리적으로 꺾이고, 제자리 회전 없이 자동차처럼 회전 반경을 그리며 주행하는지 확인합니다.

### 4.2 센서 토픽 및 오도메트리 발행 상태 점검
새 터미널에서 센서 및 오도메트리 토픽 수신 속도(Hz)와 데이터를 체크합니다.

1. **전체 토픽 목록 확인:**
   ```bash
   ros2 topic list
   ```
2. **3D-LiDAR 센서 토픽 수신 주기 점검:**
   ```bash
   ros2 topic hz /scan
   ```
   *(약 10Hz 이상 안정적으로 퍼블리시되는지 확인)*
3. **카메라 영상 토픽 수신 주기 점검:**
   ```bash
   ros2 topic hz /camera/color/image_raw
   ```
4. **오도메트리 위치 및 속도 데이터 점검:**
   ```bash
   ros2 topic echo /odom
   ```
   *(키보드 조종 시 `position`과 `orientation` 값 및 속도 데이터가 실시간으로 변하는지 확인)*

---

## 5. 검증 체크리스트

1. **시각적 조향 검증:** Gazebo 환경에서 주행 시 앞바퀴 2개가 곡선 궤적에 맞춰 좌우로 각도가 꺾이는지 확인
2. **최소 회전 반경 확인:** 차동 구동처럼 제자리 회전하지 않고 승용차처럼 큰 원을 그리며 회전하는지 확인
3. **경량 월드 확인:** 시뮬레이터가 렉 없이 쾌적하게 켜지며 회색 격자 무늬 바닥이 표시되는지 확인
4. **센서 데이터 정상 수신:** `/scan`, `/camera/color/image_raw`, `/odom` 토픽이 정상 발행되는지 확인
