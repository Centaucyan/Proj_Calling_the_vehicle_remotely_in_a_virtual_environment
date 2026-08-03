import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_hunter_gazebo = get_package_share_directory('hunter_gazebo')

    # 1. Gazebo 월드 런치 (Hunter 모델 스폰 포함)
    launch_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_hunter_gazebo, 'launch', 'launch_sim.launch.py')
        )
    )

    # 2. 3D LiDAR -> 2D LaserScan 변환 노드
    start_pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        output='screen',
        parameters=[{
            'target_frame': 'velodyne_link',
            'transform_tolerance': 0.01,
            'min_height': -0.1,
            'max_height': 1.0,
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.0087,
            'scan_time': 0.1,
            'range_min': 0.3,
            'range_max': 20.0,
            'use_sim_time': True
        }],
        remappings=[('cloud_in', '/points_raw'), ('scan', '/scan')]
    )

    # 3. Nav2 런치 포함
    launch_nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_hunter_gazebo, 'launch', 'navigation.launch.py')
        )
    )

    return LaunchDescription([
        launch_sim,
        start_pointcloud_to_laserscan_node,
        launch_nav2
    ])
