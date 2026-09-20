from collections import defaultdict


class TrajectoryService:
    """
    Maintains the movement history of each tracked person.

    Each trajectory point contains:
        frame_id
        x
        y
    """

    def __init__(self, max_history: int | None = None):
        self.max_history = max_history

        # {
        #   track_id: [
        #       {"frame_id": 1, "x": 100, "y": 200},
        #       {"frame_id": 2, "x": 105, "y": 204},
        #   ]
        # }
        self.trajectories = defaultdict(list)

    def update(self, tracking_result: dict) -> dict:
        """
        Add current track positions to trajectory history.
        """

        frame_id = tracking_result["frame_id"]

        for track in tracking_result["tracks"]:
            track_id = track["track_id"]
            center_x, center_y = track["center"]

            point = {
                "frame_id": frame_id,
                "x": float(center_x),
                "y": float(center_y),
            }

            self.trajectories[track_id].append(point)

            if (
                self.max_history is not None
                and len(self.trajectories[track_id]) > self.max_history
            ):
                self.trajectories[track_id] = (
                    self.trajectories[track_id][-self.max_history:]
                )

        return self.get_current_trajectories()

    def get_trajectory(self, track_id: int) -> list[dict]:
        """
        Return trajectory of one person.
        """

        return self.trajectories.get(track_id, [])

    def get_all_trajectories(self) -> dict[int, list[dict]]:
        """
        Return trajectories of all tracked persons.
        """

        return dict(self.trajectories)

    def get_current_trajectories(self) -> dict:
        """
        Return a JSON-friendly representation.
        """

        return {
            str(track_id): points
            for track_id, points in self.trajectories.items()
        }

    def clear(self):
        """
        Clear all trajectory history.
        """

        self.trajectories.clear()