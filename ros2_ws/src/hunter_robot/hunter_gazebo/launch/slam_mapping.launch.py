import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_hunter_gazebo = get_package_share_directory('hunter_gazebo')

    # 1. Gazebo 주차장 월드 런치 포함
    launch_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_hunter_gazebo, 'launch', 'launch_sim.launch.py')
        )
    )

    # 2. SLAM Toolbox 설정 파일 지정
    slam_config_file = os.path.join(pkg_hunter_gazebo, 'config', 'mapper_params_online_async.yaml')

    # 3. slam_toolbox 노드 실행
    start_async_slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_config_file,
            {'use_sim_time': True}
        ]
    )

    return LaunchDescription([
        launch_sim,
        start_async_slam_toolbox_node
    ])