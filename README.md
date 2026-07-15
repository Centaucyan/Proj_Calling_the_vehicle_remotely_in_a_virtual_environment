# Proj_Calling_the_vehicle_remotely_in_a_simulation_env

## 1. Description
* When a vehicle is summoned via remote control in a simulation environment, it will drive autonomously to the location of the remote control.
---

## 2. Environment
* **OS:** Ubuntu 22.04 LTS(Jammy Jellyfish)
* **Language:** C++, Python(ver: 3.12.13)
* **Middle ware:** ROS2 Humble
* **Visualization Tool:** RViz2
---

## 3. Reference
* **git repository:** https://github.com/linorobot/linorobot2
---

## 4. Pre-installation
* $ sudo apt update
* $ sudo apt upgrade 
* $ sudo apt install python3-pip
### 4.1. linorobot2
* $ mkdir -p ros2_ws/src/
* $ cd ros2_ws/src/
* $ git clone -b $ROS_DISTRO https://github.com/linorobot/linorobot2
* **[Note]** Add the following code to the 'linorobot2/linorobot2_gazebo/package.xml' file:
    * <exec_depend>python3-collada</exec_depend>
    * <exec_depend>python3-opencv</exec_depend>
* $ cd ..
* $ rosdep update && rosdep install --from-path src --ignore-src -y --skip-keys microxrcedds_agent --skip-keys micro_ros_agent --skip-keys python3-opencv-contrib-python --skip-keys python3-pycollada
* $ colcon build
* $ source install/setup.bash
* $ rm -rf ros2_ws/src/linorobot2/.git
---

## 5. ROS2 노드 구성도 (아키텍처)
![Node Architecture](./documents/images/ROS2_node_structure.png)
---