#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from robomaster import camera, robot, led
from typing import Callable, Optional, Union
#from robot import RobotController
import os
import cv2
import numpy as np
import pyarrow as pa
from utils import LABELS

from dora import DoraStatus

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

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

    def on_event(
        self,
        dora_event: str,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ) -> DoraStatus:
        event_type = dora_event["type"]
        if event_type == "INPUT":
            frame = self.ep_robot.camera.read_cv2_image()
            frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
            send_output(
                "image",
                pa.array(frame.ravel()),
                dora_event["metadata"],
            )
            return self.on_input(dora_event, send_output)
        elif event_type == "STOP":
            print("received stop")
        else:
            print("received unexpected event:", event_type)
        return DoraStatus.CONTINUE

    def on_input(
        self,
        dora_input: dict,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ) -> DoraStatus:
        print("bonjour", flush=True)
        if dora_input["id"] == "bbox":
            bboxs = dora_input["value"].to_numpy()
            self.bboxs = np.reshape(bboxs, (-1, 6))
            for bbox in self.bboxs:
                [
                    min_x, #
                    min_y,
                    max_x,
                    max_y,
                    confidence,
                    label,
                ] = bbox
                if LABELS[int(label)] == "bottle":
                    if (min_x + max_x) / 2 < 300:
                        self.ep_robot.chassis.move(x=0, y=-0.1, z=0, xy_speed=0.3).wait_for_completed()
                    elif (min_x + max_x) / 2 > 340:
                        self.ep_robot.chassis.move(x=0, y=0.1, z=0, xy_speed=0.3).wait_for_completed()
                    else:
                        self.ep_robot.chassis.move(x=0, y=0.1, z=0, xy_speed=0.3).wait_for_completed()
                    break
        return DoraStatus.CONTINUE

    def __del__(self):
        self.ep_robot.camera.stop_video_stream()
