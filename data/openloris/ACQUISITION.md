# OpenLORIS selective acquisition record

Source: `shixuesong/openloris-scene` on Hugging Face, mirroring the official
OpenLORIS-Scene release. Checked 2026-08-13.

The dataset is distributed under CC BY-ND 4.0. Derived feature tables and
labels are for local experiments; do not redistribute a modified dataset
without confirming that this complies with the no-derivatives term or obtaining
permission from the dataset owner.

The smallest grouped rosbag archive is `cafe1-1_2-rosbag.tar` (6,739,138,560
bytes). Its first tar member is:

```text
-rw-rw-r-- xuesongs/xuesongs 2558246662 2020-05-10 23:58 cafe1-1.bag
```

A tar member starts after its 512-byte header, so the exact inclusive HTTP byte
range for the bag payload is `512-2558247173`. Only that 2.558 GB range is
downloaded to `cafe1-1.bag`; the 6.74 GB tar is never materialized.

Required integrity checks after download:

```bash
stat -c '%n %s bytes' active_slam_research/data/openloris/cafe1-1.bag
rosbag info --yaml active_slam_research/data/openloris/cafe1-1.bag
rosbag reindex active_slam_research/data/openloris/cafe1-1.bag  # only if info reports a missing index
```

Expected payload size is exactly `2558246662` bytes. Do not start RTAB-Map if
the size or rosbag index check fails.

The dataset is fixed-trajectory data. It is used for health calibration and
SLAM error/failure analysis, not for closed-loop planner claims.
