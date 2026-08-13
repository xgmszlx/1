# Third-party material and data boundaries

## Git submodules

- `projects/autonomous-exploration-demo-benchmark` tracks commit
  `9dbf7bd869a9da5571c1b004a652e4b7988f348b` from
  `mertgulerx/autonomous-exploration-demo-benchmark`, licensed Apache-2.0.
- `projects/openloris-scene-tools` tracks the official OpenLORIS-Scene tools;
  consult that repository's `LICENSE.txt` for its terms.

The research code in this repository calls or reads these projects but does not
relicense them.

## OpenLORIS-Scene data

The dataset is released under CC BY-ND 4.0. Raw rosbags, databases, and
per-frame derived feature/label tables are deliberately excluded from Git.
Only small aggregate metrics written by the local experiment are retained.
Obtain the original data from the dataset owner and cite the OpenLORIS-Scene
paper when using it.

## Papers

Downloaded PDFs and extracted full text are excluded. The repository retains
bibliographic metadata, links, evidence labels, and original synthesis only.
