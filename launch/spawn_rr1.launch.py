import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler, DeclareLaunchArgument
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration

from ament_index_python.packages import get_package_share_directory

DESCRIPTION_PKG = "rr1_description"
GAZEBO_PKG = "gazebo_ros"

ROBOT_NAME = "rr1"
URDF_FILE = f"{ROBOT_NAME}.urdf.xacro"

ROBOT_POSITION = [0.0, 0.0, 0]
ROBOT_ORIENTATION = [0.0, 0.0, 0.0]

NAMESPACE = "rr1"

def generate_launch_description():
    # ------------------------------- Fetch paths ------------------------------
    # Package share directories
    description_pkg = get_package_share_directory(DESCRIPTION_PKG)
    urdf_path = os.path.join(description_pkg, "urdf", URDF_FILE)

    use_sim_time = LaunchConfiguration('use_sim_time')
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    #  --------------------------- Instantiate nodes ---------------------------
    xacro_command = Command(['xacro ', urdf_path, " ns:={}".format(NAMESPACE)])
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        namespace=NAMESPACE,
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': xacro_command}]
    )

    spawn_robot = Node(
        package=GAZEBO_PKG,
        executable='spawn_entity.py',
        name='spawn_entity',
        output='screen',
        arguments=['-entity', "{}-{}".format(ROBOT_NAME, NAMESPACE),
            '-x', str(ROBOT_POSITION[0]), '-y', str(ROBOT_POSITION[1]), '-z', str(ROBOT_POSITION[2]),
            '-R', str(ROBOT_ORIENTATION[0]), '-P', str(ROBOT_ORIENTATION[1]), '-Y', str(ROBOT_ORIENTATION[2]),
            '-topic', '/{}/robot_description'.format(NAMESPACE)
        ]
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/{}/controller_manager".format(NAMESPACE)]
    )

    forward_position_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["--inactive", "forward_position_controller", "--controller-manager", "/{}/controller_manager".format(NAMESPACE)]
    )

    joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", "--controller-manager", "/{}/controller_manager".format(NAMESPACE)]
    )

    # Ensure the correct order of starting notes
    joint_state_broadcaster_event = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[joint_state_broadcaster]
        )
    )

    forward_position_controller_event = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[forward_position_controller]
        )
    )

    joint_trajectory_controller_event = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[joint_trajectory_controller]
        )
    )

    nodes = [
        declare_use_sim_time,
        
        joint_state_broadcaster_event,
        forward_position_controller_event,
        joint_trajectory_controller_event,
        robot_state_publisher,
        spawn_robot
    ]

    return LaunchDescription(nodes)
