#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from robomaster import camera, robot, led
from typing import Callable, Optional, Union

# from robot import RobotController
import os
import cv2
import numpy as np
import pyarrow as pa
from utils import LABELS

from dora import DoraStatus
from time import sleep

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
        self.ep_robot_camera = self.ep_robot.camera
        self.ep_robot_chassis = self.ep_robot.chassis

        self.ep_robot_camera.start_video_stream(display=False)
        self.bboxs = []

    def on_event(
        self,
        dora_event: str,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ) -> DoraStatus:
        event_type = dora_event["type"]
        if event_type == "INPUT":
            if dora_event["id"] == "tick":
                print("received tick", flush=True)

                frame = self.ep_robot_camera.read_cv2_image()
                frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
                send_output(
                    "image",
                    pa.array(frame.ravel()),
                    dora_event["metadata"],
                )
            elif dora_event["id"] == "bbox":
                print("received bbox", flush=True)
                self.on_input_bbox(dora_event, send_output)
                print("Finished on bbox", flush=True)

            return DoraStatus.CONTINUE

        elif event_type == "STOP":
            print("received stop")
        else:
            print("received unexpected event:", event_type)
        return DoraStatus.CONTINUE

    def on_input_bbox(
        self,
        dora_input: dict,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ):
        bboxs = dora_input["value"].to_numpy()
        self.bboxs = np.reshape(bboxs, (-1, 6))
        isbottle = False
        for bbox in self.bboxs:
            [
                min_x,
                min_y,
                max_x,
                max_y,
                confidence,
                label,
            ] = bbox
            if LABELS[int(label)] == "bottle":
                isbottle = True
                break
        if isbottle:
            self.ep_robot.led.set_led(r=255, g=0, b=0, effect=led.EFFECT_ON)
        else:
            self.ep_robot.led.set_led(r=0, g=255, b=0, effect=led.EFFECT_ON)

    def __del__(self):
        self.ep_robot.camera.stop_video_stream()
