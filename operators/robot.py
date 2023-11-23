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
        for bbox in bboxs:
            [
                min_x,
                min_y,
                max_x,
                max_y,
                confidence,
                label,
            ] = bbox
            if LABELS[int(label)] == "bottle":
                """if (min_x + max_x) / 2 < 290:
                    self.ep_robot.chassis.drive_wheels(w1=15, w2=-15, w3=-15, w4=15)
                    time.sleep(1)
                    self.ep_robot.gimbal.recenter().wait_for_completed()
                elif (min_x + max_x) / 2 > 350:
                    self.ep_robot.chassis.drive_wheels(w1=-15, w2=15, w3=15, w4=-15)
                    time.sleep(1)
                    self.ep_robot.gimbal.recenter().wait_for_completed()"""
                if (min_x + max_x) / 2 < 290:
                    self.event = self.ep_robot.chassis.move(
                        x=0, y=-0.1, z=0, xy_speed=0.3
                    )
                elif (min_x + max_x) / 2 > 350:
                    self.event = self.ep_robot.chassis.move(
                        x=0, y=0.1, z=0, xy_speed=0.3
                    )
                else:
                    self.event = self.ep_robot.chassis.move(
                        x=0.1, y=0, z=0, xy_speed=0.3
                    )
                print("finish waiting", flush=True)
                break

    def __del__(self):
        self.ep_robot.camera.stop_video_stream()
