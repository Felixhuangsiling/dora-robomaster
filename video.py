
    

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from robomaster import camera, robot
from typing import Callable, Optional, Union

import os
import cv2
import numpy as np
import pyarrow as pa

from dora import DoraStatus

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

font = cv2.FONT_HERSHEY_SIMPLEX


class Operator:
    """
    Sending image from webcam to the dataflow
    """

    def __init__(self):
        ep_robot = robot.Robot()
        ep_robot.initialize(conn_type="ap")

        self.ep_camera = ep_robot.camera
        self.ep_camera.start_video_stream(display=False)
        self.start_time = time.time()

    def on_event(
        self,
        dora_event: str,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ) -> DoraStatus:
        event_type = dora_event["type"]
        if event_type == "INPUT":
            frame = self.ep_camera.read_cv2_image()
            frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
            send_output(
                "image",
                pa.array(frame.ravel()),
                dora_event["metadata"],
            )
        elif event_type == "STOP":
            print("received stop")
        else:
            print("received unexpected event:", event_type)


        if time.time() - self.start_time < 100:
            return DoraStatus.CONTINUE
        else:
            return DoraStatus.STOP

    def __del__(self):
        self.ep_camera.stop_video_stream()
