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
            elif dora_event["id"] == "bbox":
                self.on_input_bbox(dora_event, send_output)

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
        bboxs = np.copy(bboxs)
        self.control(bboxs)

    def control(self, bboxs):
        if self.event is not None and not (
            self.event._event.isSet() and self.event.is_completed
        ):
            return
        bboxs = np.reshape(bboxs, (-1, 6))
        obstacle = False
        box = False
        for bbox in bboxs:
            box = True
            [
                min_x,
                min_y,
                max_x,
                max_y,
                confidence,
                label,
            ] = bbox
            if (
                min_x > 276
                and min_x < 288
                and max_x > 361
                and max_x < 370
                and min_y > 422
                and min_y < 430
                and max_y > 479
            ):
                continue
            if LABELS[int(label)] == "ABC":
                continue

            if max_y > 370 and (min_x + max_x) / 2 > 240 and (min_x + max_x) / 2 < 400:
                if (min_x + max_x) / 2 > 320:
                    self.event = self.ep_robot.chassis.move(
                        x=0, y=-0.15, z=0, xy_speed=0.4
                    )
                elif (min_x + max_x) / 2 <= 320:
                    self.event = self.ep_robot.chassis.move(
                        x=0, y=0.15, z=0, xy_speed=0.4
                    )
                obstacle = True
                break
        if obstacle == False and box == True:
            self.event = self.ep_robot.chassis.move(x=0.1, y=0, z=0, xy_speed=0.5)

    def __del__(self):
        self.ep_robot.camera.stop_video_stream()
