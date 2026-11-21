import math


class MovementService:
    """
    Calculates movement features from person trajectories.

    Velocity is expressed in pixels/second when FPS is known.

    Only currently active tracks should be passed to
    calculate_all() during frame-level analysis.
    """

    def __init__(self, fps: float | None = None):
        if fps is not None and fps <= 0:
            raise ValueError("FPS must be greater than zero.")

        self.fps = fps

    @staticmethod
    def _direction(dx: float, dy: float) -> str:
        if dx == 0 and dy == 0:
            return "STATIONARY"

        angle = math.degrees(math.atan2(-dy, dx))

        if angle < 0:
            angle += 360

        if angle >= 337.5 or angle < 22.5:
            return "RIGHT"

        if angle < 67.5:
            return "UP_RIGHT"

        if angle < 112.5:
            return "UP"

        if angle < 157.5:
            return "UP_LEFT"

        if angle < 202.5:
            return "LEFT"

        if angle < 247.5:
            return "DOWN_LEFT"

        if angle < 292.5:
            return "DOWN"

        return "DOWN_RIGHT"

    def calculate_track_movement(
        self,
        trajectory: list[dict],
    ) -> dict:

        # -----------------------------------------
        # Not enough trajectory information
        # -----------------------------------------

        if len(trajectory) < 2:
            return {
                "displacement": 0.0,
                "speed": None,
                "direction": "UNKNOWN",
                "dx": 0.0,
                "dy": 0.0,
                "frame_delta": 0,
            }

        previous = trajectory[-2]
        current = trajectory[-1]

        dx = (
            float(current["x"])
            - float(previous["x"])
        )

        dy = (
            float(current["y"])
            - float(previous["y"])
        )

        displacement = math.sqrt(
            (dx * dx) + (dy * dy)
        )

        frame_delta = (
            int(current["frame_id"])
            - int(previous["frame_id"])
        )

        speed = None

        if (
            self.fps is not None
            and frame_delta > 0
        ):
            time_seconds = (
                frame_delta / self.fps
            )

            speed = (
                displacement
                / time_seconds
            )

        direction = self._direction(
            dx,
            dy,
        )

        return {
            "displacement": float(
                displacement
            ),
            "speed": (
                float(speed)
                if speed is not None
                else None
            ),
            "direction": direction,
            "dx": float(dx),
            "dy": float(dy),
            "frame_delta": frame_delta,
        }

    def calculate_all(
        self,
        trajectories: dict[int, list[dict]],
        active_track_ids: set[int] | None = None,
    ) -> dict:

        """
        Calculate movement only for active/current tracks.

        active_track_ids:
            IDs currently visible in the current frame.

        If active_track_ids is None, all supplied trajectories
        are processed for backward compatibility.
        """

        results = {}

        if active_track_ids is None:
            active_track_ids = set(
                trajectories.keys()
            )

        for track_id, trajectory in trajectories.items():

            track_id = int(track_id)

            if track_id not in active_track_ids:
                continue

            results[track_id] = (
                self.calculate_track_movement(
                    trajectory
                )
            )

        return results

    def aggregate(
        self,
        movement_results: dict[int, dict],
    ) -> dict:

        if not movement_results:
            return {
                "tracked_persons": 0,
                "moving_persons": 0,
                "stationary_persons": 0,
                "unknown_persons": 0,
                "average_speed": None,
                "average_displacement": 0.0,
            }

        speeds = [
            result["speed"]
            for result in movement_results.values()
            if result.get("speed") is not None
        ]

        displacements = [
            result.get(
                "displacement",
                0.0,
            )
            for result in movement_results.values()
        ]

        stationary = sum(
            1
            for result in movement_results.values()
            if result.get("direction")
            == "STATIONARY"
        )

        unknown = sum(
            1
            for result in movement_results.values()
            if result.get("direction")
            == "UNKNOWN"
        )

        moving = sum(
            1
            for result in movement_results.values()
            if result.get("direction")
            not in (
                "STATIONARY",
                "UNKNOWN",
            )
        )

        return {
            "tracked_persons": len(
                movement_results
            ),

            "moving_persons": moving,

            "stationary_persons": stationary,

            "unknown_persons": unknown,

            "average_speed": (
                sum(speeds) / len(speeds)
                if speeds
                else None
            ),

            "average_displacement": (
                sum(displacements)
                / len(displacements)
                if displacements
                else 0.0
            ),
        }