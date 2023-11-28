#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from robomaster import robot
from typing import Callable, Optional, Union

# from robot import RobotController
import cv2
import numpy as np
import pyarrow as pa
from utils import LABELS

from dora import DoraStatus

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
ROBOT_HEIGHT = 0.22
font = cv2.FONT_HERSHEY_SIMPLEX


class Operator:
    """
    Sending image from webcam to the dataflow
    """

    def __init__(self):
        self.ep_robot = robot.Robot()
        self.ep_robot.initialize(conn_type="ap")
        self.ep_robot.camera.start_video_stream(display=False)
        self.bboxs = []
        self.event = None

    def on_event(
        self,
        dora_event: str,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ) -> DoraStatus:
        event_type = dora_event["type"]
        if event_type == "INPUT":
            if dora_event["id"] == "tick":
                frame = self.ep_robot.camera.read_cv2_image(
                    timeout=1, strategy="newest"
                )
                frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
                send_output(
                    "image",
                    pa.array(frame.ravel()),
                    dora_event["metadata"],
                )
            elif dora_event["id"] == "control":
                if not (
                    self.event is not None
                    and not (self.event._event.isSet() and self.event.is_completed)
                ):
                    [x, y, z, speed] = dora_event["value"].to_numpy()
                    self.event = self.ep_robot.chassis.move(
                        x=x, y=y, z=z, xy_speed=speed
                    )

            return DoraStatus.CONTINUE

        elif event_type == "STOP":
            print("received stop")
        else:
            print("received unexpected event:", event_type)
        return DoraStatus.CONTINUE

    def __del__(self):
        self.ep_robot.camera.stop_video_stream()
