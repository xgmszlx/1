#!/usr/bin/env python3
"""Repeat a static CameraInfo with each image timestamp for message filters.

OpenLORIS stores calibration once, while RTAB-Map's RGB-D/scan synchronizer
expects CameraInfo in each synchronized tuple. Intrinsics are not modified.
"""

from __future__ import annotations

import copy

import rospy
from sensor_msgs.msg import CameraInfo, Image


class CameraInfoRepeater:
    def __init__(self) -> None:
        self._camera_info: CameraInfo | None = None
        output_topic = rospy.get_param("~output_topic", "/d400/color/camera_info_repeated")
        input_info_topic = rospy.get_param("~input_info_topic", "/d400/color/camera_info")
        image_topic = rospy.get_param("~image_topic", "/d400/color/image_raw")
        self._publisher = rospy.Publisher(output_topic, CameraInfo, queue_size=10)
        rospy.Subscriber(input_info_topic, CameraInfo, self._info_callback, queue_size=1)
        rospy.Subscriber(image_topic, Image, self._image_callback, queue_size=20)

    def _info_callback(self, message: CameraInfo) -> None:
        self._camera_info = message

    def _image_callback(self, message: Image) -> None:
        if self._camera_info is None:
            return
        repeated = copy.deepcopy(self._camera_info)
        repeated.header = message.header
        self._publisher.publish(repeated)


def main() -> None:
    rospy.init_node("openloris_camera_info_repeater")
    CameraInfoRepeater()
    rospy.spin()


if __name__ == "__main__":
    main()
