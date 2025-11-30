"""
MAVLink Message Decoders

This module provides functions to decode numeric MAVLink message fields
into human-readable names based on official MAVLink enum definitions.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


# MAV_TYPE - Vehicle/Component type enumeration
# Reference: https://mavlink.io/en/messages/common.html#MAV_TYPE
MAV_TYPE_MAP = {
    0: "GENERIC",
    1: "FIXED_WING",
    2: "QUADROTOR",
    3: "COAXIAL",
    4: "HELICOPTER",
    5: "ANTENNA_TRACKER",
    6: "GCS",
    7: "AIRSHIP",
    8: "FREE_BALLOON",
    9: "ROCKET",
    10: "GROUND_ROVER",
    11: "SURFACE_BOAT",
    12: "SUBMARINE",
    13: "HEXAROTOR",
    14: "OCTOROTOR",
    15: "TRICOPTER",
    16: "FLAPPING_WING",
    17: "KITE",
    18: "ONBOARD_CONTROLLER",
    19: "VTOL_DUOROTOR",
    20: "VTOL_QUADROTOR",
    21: "VTOL_TILTROTOR",
    22: "VTOL_FIXEDROTOR",
    23: "VTOL_TAILSITTER",
    24: "VTOL_RESERVED4",
    25: "VTOL_RESERVED5",
    26: "GIMBAL",
    27: "ADSB",
    28: "PARAFOIL",
    29: "DODECAROTOR",
    30: "CAMERA",
    31: "CHARGING_STATION",
    32: "FLARM",
    33: "SERVO",
    34: "ODID",
    35: "DECAROTOR",
    36: "BATTERY",
    37: "PARACHUTE",
    38: "LOG",
    39: "OSD",
    40: "IMU",
    41: "GPS",
    42: "WINCH",
    43: "GENERATOR",
    44: "MOTOR_TEST",
    45: "HELI_TAIL",
    46: "HELI_CONTROL",
}


# MAV_AUTOPILOT - Autopilot type enumeration
# Reference: https://mavlink.io/en/messages/common.html#MAV_AUTOPILOT
MAV_AUTOPILOT_MAP = {
    0: "GENERIC",
    1: "RESERVED",
    2: "SLUGS",
    3: "ARDUPILOTMEGA",
    4: "OPENPILOT",
    5: "GENERIC_WAYPOINTS_ONLY",
    6: "GENERIC_WAYPOINTS_AND_SIMPLE_NAVIGATION_ONLY",
    7: "GENERIC_MISSION_FULL",
    8: "INVALID",
    9: "PPZ",
    10: "UDB",
    11: "FP",
    12: "PX4",
    13: "SMACCMPILOT",
    14: "AUTOQUAD",
    15: "ARMAZILA",
    16: "AEROB",
    17: "ASLUAV",
    18: "SMARTAP",
    19: "AIRRAILS",
    20: "REFLEX",
    21: "Naza",
    22: "TAU",
    23: "ICAROUS",
    24: "DAISA",
    25: "APM_PLANNER",
    26: "AUTERION",
    27: "PAPARAZZI",
    28: "ENDR",
    29: "GIMBAL",
    30: "MISSION_PLANNER",
    31: "QGROUNDCONTROL",
    32: "NAVIO2",
    33: "OPENDRONEID",
    34: "TAISYNC",
    35: "WFB",
    36: "NOOPAUTOLAND",
    37: "MAGIC",
    38: "APM_COPTER",
    39: "APM_ROVER",
    40: "APM_PLANE",
}


# MAV_STATE - System state enumeration
# Reference: https://mavlink.io/en/messages/common.html#MAV_STATE
MAV_STATE_MAP = {
    0: "UNINIT",
    1: "BOOT",
    2: "CALIBRATING",
    3: "STANDBY",
    4: "ACTIVE",
    5: "CRITICAL",
    6: "EMERGENCY",
    7: "POWEROFF",
    8: "FLIGHT_TERMINATION",
}


# MAV_MODE_FLAG - Mode flags (bitmask for base_mode)
# Reference: https://mavlink.io/en/messages/common.html#MAV_MODE_FLAG
# These are bit flags that can be combined in base_mode
MAV_MODE_FLAG_MAP = {
    128: "MAV_MODE_FLAG_SAFETY_ARMED",
    64: "MAV_MODE_FLAG_MANUAL_INPUT_ENABLED",
    32: "MAV_MODE_FLAG_HIL_ENABLED",
    16: "MAV_MODE_FLAG_STABILIZE_ENABLED",
    8: "MAV_MODE_FLAG_GUIDED_ENABLED",
    4: "MAV_MODE_FLAG_AUTO_ENABLED",
    2: "MAV_MODE_FLAG_TEST_ENABLED",
    1: "MAV_MODE_FLAG_CUSTOM_MODE_ENABLED",
}


# ArduCopter Flight Modes (custom_mode values for ArduCopter)
# Reference: ArduPilot documentation
# These are the standard ArduCopter flight modes
ARDUCOPTER_MODE_MAP = {
    0: "STABILIZE",
    1: "ACRO",
    2: "ALT_HOLD",
    3: "AUTO",
    4: "GUIDED",
    5: "LOITER",
    6: "RTL",
    7: "CIRCLE",
    9: "LAND",
    10: "OF_LOITER",
    11: "DRIFT",
    13: "SPORT",
    14: "FLIP",
    15: "AUTOTUNE",
    16: "POSHOLD",
    17: "BRAKE",
    18: "THROW",
    19: "AVOID_ADSB",
    20: "GUIDED_NOGPS",
    21: "SMART_RTL",
    22: "FLOWHOLD",
    23: "FOLLOW",
    24: "ZIGZAG",
    25: "SYSTEMID",
    26: "HELI_RATE",
    27: "HELI_ATT",
    28: "HELI_RATT",
    29: "HELI_ACRO",
    30: "HELI_STABILIZE",
    31: "HELI_HOVER",
    32: "HELI_LOITER",
    33: "HELI_RTL",
    34: "HELI_CIRCLE",
    35: "HELI_LAND",
    36: "HELI_FLIP",
    37: "HELI_ACRO_YAW",
    38: "HELI_AUTOTUNE",
    39: "HELI_LOITER_ALT",
    40: "HELI_POSHOLD",
    41: "HELI_BRAKE",
    42: "HELI_THROW",
    43: "HELI_AVOID_ADSB",
    44: "HELI_GUIDED_NOGPS",
    45: "HELI_SMART_RTL",
    46: "HELI_FLOWHOLD",
    47: "HELI_FOLLOW",
    48: "HELI_ZIGZAG",
    49: "HELI_SYSTEMID",
}


def decode_base_mode_flags(base_mode: int) -> List[str]:
    """
    Decode base_mode bitmask into a list of enabled flag names.
    
    The base_mode field is a bitmask where each bit represents a different
    mode flag. This function checks each bit and returns a list of enabled flags.
    
    Args:
        base_mode: Integer bitmask value from HEARTBEAT.base_mode
        
    Returns:
        List of enabled flag names (e.g., ["MAV_MODE_FLAG_SAFETY_ARMED", ...])
    """
    flags = []
    
    # Check each flag bit in descending order (most significant first)
    for flag_value, flag_name in sorted(MAV_MODE_FLAG_MAP.items(), reverse=True):
        if base_mode & flag_value:
            flags.append(flag_name)
    
    return flags


def decode_arducopter_flight_mode(custom_mode: int) -> str:
    """
    Decode ArduCopter custom_mode value to flight mode name.
    
    The custom_mode field in HEARTBEAT contains the flight mode number
    which is specific to the autopilot type. For ArduPilot (autopilot=3),
    this represents the ArduCopter flight mode.
    
    Args:
        custom_mode: Integer flight mode value from HEARTBEAT.custom_mode
        
    Returns:
        Flight mode name (e.g., "STABILIZE", "AUTO", "GUIDED") or "UNKNOWN"
    """
    return ARDUCOPTER_MODE_MAP.get(custom_mode, "UNKNOWN")


def decode_heartbeat(msg_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decode HEARTBEAT message by adding human-readable fields.
    
    This function takes a HEARTBEAT message dictionary (from _message_to_dict)
    and adds decoded fields with human-readable names while preserving all
    original numeric fields.
    
    Args:
        msg_dict: Dictionary containing HEARTBEAT message fields
        
    Returns:
        Enhanced dictionary with original fields plus decoded fields:
        - type_name: Vehicle type name (from MAV_TYPE)
        - autopilot_name: Autopilot name (from MAV_AUTOPILOT)
        - system_status_name: System status name (from MAV_STATE)
        - base_mode_flags: List of enabled mode flags (from MAV_MODE_FLAG)
        - flight_mode_name: Flight mode name (from ArduCopter modes)
    """
    # Create a copy to avoid modifying the original
    decoded = msg_dict.copy()
    
    # Decode type field (vehicle type - MAV_TYPE)
    # Check for mav_type first (preserved before override), then type field
    mav_type = msg_dict.get("mav_type", None)
    
    if mav_type is not None:
        # Use the preserved MAV_TYPE value
        decoded["type_name"] = MAV_TYPE_MAP.get(mav_type, "UNKNOWN")
    else:
        # Fallback: check if type is numeric (in case mav_type wasn't preserved)
        type_value = msg_dict.get("type", None)
        if isinstance(type_value, int):
            # This is the MAV_TYPE numeric value
            decoded["type_name"] = MAV_TYPE_MAP.get(type_value, "UNKNOWN")
        elif isinstance(type_value, str):
            # This is the message name ("HEARTBEAT"), not MAV_TYPE
            # We can't decode it, so keep it as is
            decoded["type_name"] = type_value
            logger.warning(f"Cannot decode MAV_TYPE - type is string '{type_value}', mav_type was not preserved")
        else:
            decoded["type_name"] = "UNKNOWN"
            logger.warning(f"Cannot decode MAV_TYPE - type is {type(type_value)}")
    
    # Decode autopilot field
    autopilot = msg_dict.get("autopilot", None)
    if autopilot is not None:
        decoded["autopilot_name"] = MAV_AUTOPILOT_MAP.get(autopilot, "UNKNOWN")
    else:
        logger.warning("autopilot field is None or missing")
    
    # Decode system_status field
    system_status = msg_dict.get("system_status", None)
    if system_status is not None:
        decoded["system_status_name"] = MAV_STATE_MAP.get(system_status, "UNKNOWN")
    else:
        logger.warning("system_status field is None or missing")
    
    # Decode base_mode flags
    base_mode = msg_dict.get("base_mode", None)
    if base_mode is not None:
        decoded["base_mode_flags"] = decode_base_mode_flags(base_mode)
    else:
        logger.warning("base_mode field is None or missing")
    
    # Decode custom_mode (flight mode) - assuming ArduCopter for now
    # In the future, this could be made autopilot-aware
    custom_mode = msg_dict.get("custom_mode", None)
    if custom_mode is not None:
        decoded["flight_mode_name"] = decode_arducopter_flight_mode(custom_mode)
    else:
        logger.warning("custom_mode field is None or missing")
    return decoded


def decode_mavlink_message(msg_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic entry point for decoding MAVLink messages.
    
    This function inspects the message type and routes to the appropriate
    decoder function. Currently supports HEARTBEAT decoding, with room
    for future expansion to other message types.
    
    Args:
        msg_dict: Dictionary containing MAVLink message fields (from _message_to_dict)
        
    Returns:
        Decoded dictionary with human-readable fields added, or original dict
        if no decoder is available for this message type.
    """
    # Get message type - check message_type first (preserved name), then type field
    msg_type = msg_dict.get("message_type", None)
    if msg_type is None:
        msg_type = msg_dict.get("type", None)
    
    if msg_type == "HEARTBEAT":
        return decode_heartbeat(msg_dict)
    
    # For other message types, return unchanged (ready for future decoders)
    # Future decoders can be added here:
    # elif msg_type == "SYS_STATUS":
    #     return decode_sys_status(msg_dict)
    # elif msg_type == "BATTERY_STATUS":
    #     return decode_battery_status(msg_dict)
    return msg_dict
