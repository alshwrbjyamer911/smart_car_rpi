#!/usr/bin/python3
"""
qr.py — QR Scanner module
Automatically uses Picamera2 on Raspberry Pi (if available),
falls back to OpenCV VideoCapture on PC/dev environment.
"""

import cv2
import time
from pyzbar.pyzbar import decode

# -------------------------------------------------------
# Detect if we are running on a Raspberry Pi with picamera2
# -------------------------------------------------------
try:
    from picamera2 import Picamera2
    _PICAMERA2_AVAILABLE = True
except (ImportError, RuntimeError):
    _PICAMERA2_AVAILABLE = False
    print("[qr] picamera2 not available – using OpenCV VideoCapture (PC mode)")


class QRScanner:
    def __init__(self, device="/dev/video0", show_preview=True):
        """
        Args:
            device    : OpenCV device index or path (used only in PC mode)
            show_preview : If True, display frame via cv2.imshow inside read_qr()
        """
        self.show_preview = show_preview
        self._picam = None
        self._cap = None

        if _PICAMERA2_AVAILABLE:
            # ---- Raspberry Pi: use Picamera2 ----
            # Simple init that matches the working test — no configure() needed
            self._picam = Picamera2()
            self._picam.start()
            time.sleep(1)   # let sensor stabilise
            print("[qr] Picamera2 started (RPi mode)")
        else:
            # ---- PC: use OpenCV webcam ----
            self._cap = cv2.VideoCapture(device)
            if not self._cap.isOpened():
                raise Exception(f"Cannot open camera: {device}")
            print(f"[qr] OpenCV VideoCapture opened: {device} (PC mode)")

    # ------------------------------------------------------------------
    def read_qr(self):
        """
        Capture one frame, detect QR codes, optionally show preview.

        Returns:
            qr_data (str or None) : decoded QR string, or None if nothing found
            frame   (np.ndarray)  : annotated BGR frame (for external display too)
        """
        frame = self._capture_frame()
        if frame is None:
            return None, None

        # Work on a copy so we always return the clean+annotated frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        qr_codes = decode(gray)

        qr_data = None

        for qr in qr_codes:
            qr_data = qr.data.decode("utf-8")

            # Draw polygon
            points = qr.polygon
            pts = [(p.x, p.y) for p in points]
            for i in range(len(pts)):
                cv2.line(frame, pts[i], pts[(i + 1) % len(pts)], (0, 255, 0), 3)

            cv2.putText(
                frame,
                qr_data,
                (qr.rect.left, qr.rect.top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        # Show preview window on screen (works on both RPi desktop and PC)
        if self.show_preview and frame is not None:
            cv2.imshow("Smart Car - Camera", frame)  # ASCII dash avoids encoding glitch
            cv2.waitKey(1)   # 1 ms pump — keeps the window alive without blocking

        return qr_data, frame

    # ------------------------------------------------------------------
    def _capture_frame(self):
        """Internal: grab a BGR frame from whichever backend is active."""
        if self._picam is not None:
            # No color conversion — picamera2 default output works with cv2 directly
            return self._picam.capture_array()
        else:
            ret, frame = self._cap.read()
            return frame if ret else None

    # ------------------------------------------------------------------
    def release(self):
        """Release camera resources."""
        if self._picam is not None:
            self._picam.stop()
            self._picam.close()
        if self._cap is not None:
            self._cap.release()
        cv2.destroyAllWindows()