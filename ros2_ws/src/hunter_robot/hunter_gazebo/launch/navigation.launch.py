import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_hunter_gazebo = get_package_share_directory('hunter_gazebo')

    map_yaml_file = LaunchConfiguration('map')
    nav_params_file = LaunchConfiguration('nav_params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_hunter_gazebo, 'maps', 'parking_garage_map.yaml'),
        description='Full path to map yaml file to load')

    declare_nav_params_file_cmd = DeclareLaunchArgument(
        'nav_params_file',
        default_value=os.path.join(pkg_hunter_gazebo, 'config', 'nav2_params.yaml'),
        description='Full path to the ROS2 parameters file to use for all launched nodes')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    # Nav2 노드 리스트 실행
    start_map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[nav_params_file, {'yaml_filename': map_yaml_file, 'use_sim_time': use_sim_time}])

    start_amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])

    start_planner_node = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])

    start_controller_node = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])
    
    start_behavior_server_node = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])

    start_bt_navigator_node = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[nav_params_file, {'use_sim_time': use_sim_time}])

    start_lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time},
                    {'autostart': True},
                    {'node_names': ['map_server', 'amcl', 'planner_server', 'controller_server', 'behavior_server', 'bt_navigator']}])

    return LaunchDescription([
        declare_map_yaml_cmd,
        declare_nav_params_file_cmd,
        declare_use_sim_time_cmd,
        start_map_server_node,
        start_amcl_node,
        start_planner_node,
        start_controller_node,
        start_behavior_server_node,
        start_bt_navigator_node,
        start_lifecycle_manager
    ])
