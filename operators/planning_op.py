#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Optional, Union

import numpy as np
import pyarrow as pa
import torch
from utils import LABELS
from dora import DoraStatus

pa.array([])

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


class Operator:
    """
    Infering object from images
    """

    def on_event(
        self,
        dora_event: dict,
        send_output: Callable[[str, Union[bytes, pa.Array], Optional[dict]], None],
    ) -> DoraStatus:
        if dora_event["type"] == "INPUT":
            return self.on_input(dora_event, send_output)
        return DoraStatus.CONTINUE

    def on_input(
        self,
        dora_input: dict,
        send_output: Callable[[str, Union[bytes, pa.array], Optional[dict]], None],
    ) -> DoraStatus:
        bboxs = dora_input["value"].to_numpy()
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
                    arrays = pa.array([0, -0.15, 0, 0.4])
                    send_output("control", arrays, dora_input["metadata"])
                elif (min_x + max_x) / 2 <= 320:
                    arrays = pa.array([0, 0.15, 0, 0.4])
                    send_output("control", arrays, dora_input["metadata"])
                obstacle = True
                break
        if obstacle == False and box == True:
            arrays = pa.array([0.1, 0, 0, 0.5])
            send_output("control", arrays, dora_input["metadata"])

        return DoraStatus.CONTINUE
