# 2단계: 아커만 조향(Ackermann Steering) 신규 로봇 모델 구축 가이드

본 문서는 기존 차동 구동(Diff Drive) 대신 실제 승용차 형태의 **4륜 아커만 조향(Ackermann Steering)** 로봇 모델(`ackermann.urdf.xacro`)과 컨트롤러를 신규 추가하고 Gazebo 시뮬레이션 환경에서 검증하는 상세 가이드입니다.

---

## 1. 신규 생성 파일 개요

1. **[컨트롤러 정의 파일]** `linorobot2_description/urdf/controllers/ackermann_drive.urdf.xacro`
   - Gazebo에서 앞바퀴 조향(Steering Hinge) 및 뒷바퀴 구동을 제어하는 `gazebo_ros_ackermann_drive` 플러그인 설정
2. **[로봇 모델 정의 파일]** `linorobot2_description/urdf/robots/ackermann.urdf.xacro`
   - 4륜 차체 구조, 전륜 조향 링크/조인트, 후륜 구동 휠, 3D-LiDAR, 카메라 센서를 통합한 완성형 URDF 정의

---

## 2. 파일별 코드 상세 내용

### ① `linorobot2_description/urdf/controllers/ackermann_drive.urdf.xacro`

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://ros.org/wiki/xacro">
  <xacro:macro name="ackermann_drive" params="wheel_diameter wheel_base wheel_separation max_steer_angle">
    <gazebo>
      <plugin name="ackermann_drive" filename="libgazebo_ros_ackermann_drive.so">
        <ros>
          <remapping>cmd_vel:=cmd_vel</remapping>
          <remapping>odom:=odom</remapping>
        </ros>

        <update_rate>100.0</update_rate>

        <!-- 조인트 정의 -->
        <front_left_joint>front_left_steer_joint</front_left_joint>
        <front_right_joint>front_right_steer_joint</front_right_joint>
        <rear_left_joint>rear_left_wheel_joint</rear_left_joint>
        <rear_right_joint>rear_right_wheel_joint</rear_right_joint>

        <!-- 제원 및 PID 파라미터 -->
        <left_steering_pid_gain>1500 0 1</left_steering_pid_gain>
        <left_steering_i_limit>0 0</left_steering_i_limit>
        <right_steering_pid_gain>1500 0 1</right_steering_pid_gain>
        <right_steering_i_limit>0 0</right_steering_i_limit>
        <linear_velocity_pid_gain>100 0 1</linear_velocity_pid_gain>
        <linear_velocity_i_limit>0 0</linear_velocity_i_limit>

        <wheel_separation>${wheel_separation}</wheel_separation>
        <wheel_diameter>${wheel_diameter}</wheel_diameter>
        <max_steer>${max_steer_angle}</max_steer>
        <max_steer_rate>1.5</max_steer_rate>

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

### ② `linorobot2_description/urdf/robots/ackermann.urdf.xacro`

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
  <xacro:property name="wheel_pos_x" value="0.18" />  <!-- 휠베이스 축거 기준 -->
  <xacro:property name="wheel_pos_y" value="0.16" />  <!-- 윤거 트레드 기준 -->
  <xacro:property name="wheel_pos_z" value="-0.02" />
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

  <!-- 프레임, 센서, 아커만 제어 플러그인 로드 -->
  <xacro:base length="${base_length}" width="${base_width}" height="${base_height}" mass="${base_mass}" wheel_radius="${wheel_radius}" wheel_pos_z="${wheel_pos_z}" />
  <xacro:imu/>
  <xacro:generic_laser><xacro:insert_block name="laser_pose" /></xacro:generic_laser>
  <xacro:depth_sensor><xacro:insert_block name="depth_sensor_pose" /></xacro:depth_sensor>

  <xacro:ackermann_drive 
    wheel_diameter="${wheel_radius * 2}" 
    wheel_base="${wheel_pos_x * 2}" 
    wheel_separation="${wheel_pos_y * 2}" 
    max_steer_angle="${max_steer_angle}" 
  />
</robot>
```

---

## 3. 적용 및 실행 명령어

작성된 파일들을 바탕으로 빌드 및 시뮬레이션을 구동합니다.

```bash
# 1. ROS2 워크스페이스 이동 및 패키지 빌드
cd ~/Tae_ws/Proj_Calling_the_vehicle_remotely_in_a_virtual_environment/ros2_ws
colcon build --packages-select linorobot2_description linorobot2_gazebo
source install/setup.bash

# 2. LINOROBOT2_BASE를 ackermann으로 지정하여 Gazebo 실행
export LINOROBOT2_BASE=ackermann
ros2 launch linorobot2_gazebo gazebo.launch.py
```

---

## 4. 검증 체크리스트

1. **시각적 조향 검증:** Gazebo 환경에서 주행 시 앞바퀴 2개가 곡선 궤적에 맞춰 좌우로 각도가 꺾이는지 확인
2. **최소 회전 반경 확인:** 차동 구동처럼 제자리 회전하지 않고 승용차처럼 큰 원을 그리며 회전하는지 확인
3. **토픽 검증:** `/scan`(3D-LiDAR), `/camera/image_raw`, `/odom`(오도메트리) 토픽이 정상 발행되는지 모니터링
