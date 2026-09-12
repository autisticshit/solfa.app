"""
OMR (Optical Music Recognition) wrapper.
Runs oemer on an input image and returns the path to the generated MusicXML.
"""
import subprocess
import os
import tempfile
import glob


def image_to_musicxml(image_path: str) -> str:
    """
    Run oemer on the given image file and return the path to the
    resulting MusicXML file.
    """
    out_dir = tempfile.mkdtemp(prefix="oemer_out_")

    # oemer CLI: oemer <image_path> -o <output_dir>
    cmd = ["oemer", image_path, "-o", out_dir]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if proc.returncode != 0:
        raise RuntimeError(
            f"oemer failed (code {proc.returncode}):\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )

    xml_candidates = glob.glob(os.path.join(out_dir, "*.musicxml")) + \
        glob.glob(os.path.join(out_dir, "*.xml"))

    if not xml_candidates:
        raise RuntimeError(
            f"oemer produced no MusicXML output. stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )

    return xml_candidates[0]
