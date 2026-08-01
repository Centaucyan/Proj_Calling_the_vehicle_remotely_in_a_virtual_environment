import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node


def generate_launch_description():

    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    # 1. Robot State Publisher 런치
    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('hunter_description'),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'true'}.items()
    )


    # 2. parking_garage.world 파일 경로 지정(By Tae)
    world_file_path = os.path.join(
        get_package_share_directory('hunter_gazebo'), 'worlds', 'parking_garage.world'
    )

    gazebo_params_file = os.path.join(
        get_package_share_directory('hunter_gazebo'),'config','gazebo_params.yaml'
    )

    # 3. Gazebo Launch (world 파라미터 전달)
    # Include the Gazebo launch file, provided by the gazebo_ros package
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
                    #.(주차장 World 파일 적용으로 주석 처리) launch_arguments={'extra_gazebo_args': '--ros-args --params-file ' + gazebo_params_file}.items()
                    launch_arguments={
                        'world': world_file_path,
                        'extra_gazebo_args': '--ros-args --params-file ' + gazebo_params_file
                    }.items()
             )

    # 4. AgileX Hunter 로봇 스폰 (주차장 입구 스폰)
    # Run the spawner node from the gazebo_ros package. The entity name doesn't really matter if you only have a single robot.
    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', 'hunter_gazebo',
                                #. (주차장 World 파일 적용으로 추석 처리)    '-z', '0.25'],
                                   '-x', '0.0', '-y', '-8.0', '-z', '0.25'],
                        output='screen')


    # diff_drive_spawner = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=["diff_drive_controller"],
    # )

    # [수정 코드] 아커만 스포너 노드로 지정 🌟
    ackermann_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["ackermann_steering_controller"],
        remappings=[
            ("/ackermann_steering_controller/reference_unstamped", "/cmd_vel"),
        ]
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )


    # Launch them all!
    return LaunchDescription([
        rsp,
        gazebo,
        spawn_entity,
        # diff_drive_spawner,
        ackermann_spawner,  #. 아커만 스포너 적용
        joint_broad_spawner
    ])
